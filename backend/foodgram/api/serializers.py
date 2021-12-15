from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from api.fields import Base64ToImageField
from api.utils import (check_id_list, check_ingredients_data,
                       get_ingredients_objects)
from organizer.models import Favorite, ShoppingCart, Subscription
from recipes.models import Ingredient, Measurement, Recipe, Tag
from users.models import User

AMOUNT_ERROR_MESSAGE = ('количество ингредиента укажите числом с точкой в '
                        'качестве разделителя десятичной части.')
REQUIRED_FIELD = 'Обязательное поле.'


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = ('id', 'name', 'measurement_unit')


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.CharField(
        source='measurement.measurement_unit'
    )
    name = serializers.CharField(source='measurement.name')
    amount = serializers.SerializerMethodField()
    id = serializers.IntegerField(source='measurement.id')

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_amount(self, object):
        return object.amount.normalize()

    def to_internal_value(self, data):
        ingredients_errors = check_ingredients_data([data])
        if ingredients_errors:
            raise serializers.ValidationError(ingredients_errors)
        return data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')

    def to_internal_value(self, data):
        tag_errors = check_id_list(Tag, [data])
        if tag_errors:
            raise serializers.ValidationError(tag_errors)
        return data


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed'
        )

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        validated_data['password'] = make_password(
            validated_data.get('password')
        )
        return super().create(validated_data)

    def get_is_subscribed(self, object):
        user = self.context.get('request').user
        return Subscription.objects.filter(
            user=user.id, author=object
        ).exists()


class UserPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    current_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate_current_password(self, value):
        user = get_object_or_404(User, pk=self.context.user.id)
        if not user.check_password(value):
            raise serializers.ValidationError('Текущий пароль неверный.')
        return value


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    image = Base64ToImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше нуля.'
            )
        return value

    def validate(self, data):
        # Проверка наличия в базе Рецепта, похожего на сохраняемый.
        # Сперва извлекаем image, т.к. передаётся в виде ContentType, который
        # меняется с каждым запросом:
        is_image_in_data = False
        if 'image' in data:
            is_image_in_data = True
            image = data.pop('image')
        tags = data.pop('tags')
        # ингредиенты не учитываем при проверке уникальности:
        ingredients = data.pop('ingredients')
        # проверка уникальности рецепта только при POST-запросе:
        if (self.context.get('request').method == 'POST'
                and Recipe.objects.filter(tags__id__in=tags, **data).exists()):
            raise serializers.ValidationError({
                'errors': 'У вас уже есть такой рецепт.'
            })
        # проверка наличия повторяющихся ингредиентов:
        ingredients_ids = [ingredient.get('id') for ingredient in ingredients]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError({
                'errors': 'Ингредиенты не должны повторяться.'
            })

        if is_image_in_data:
            data['image'] = image
        data['tags'] = tags
        data['ingredients'] = ingredients
        return data

    def create(self, validated_data):
        tag_list = validated_data.pop('tags')
        if tag_list:
            tags_objects = [
                get_object_or_404(Tag, pk=tag_id) for tag_id in tag_list
            ]

        ingredients_list = validated_data.pop('ingredients')
        ingredients_objects = get_ingredients_objects(ingredients_list)

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_objects)
        recipe.ingredients.set(ingredients_objects)
        return recipe

    def update(self, instance, validated_data):
        tag_list = validated_data.pop('tags')
        if tag_list:
            tags_objects = [
                get_object_or_404(Tag, pk=tag_id) for tag_id in tag_list
            ]
            instance.tags.set(tags_objects)

        ingredients_list = validated_data.pop('ingredients')
        ingredients_objects = get_ingredients_objects(ingredients_list)
        instance.ingredients.set(ingredients_objects)

        return super().update(instance, validated_data)

    def get_is_favorited(self, object):
        user = self.context.get('request').user
        return Favorite.objects.filter(user=user.id, recipe=object.id).exists()

    def get_is_in_shopping_cart(self, object):
        user = self.context.get('request').user
        return ShoppingCart.objects.filter(
            user=user.id, recipe=object.id
        ).exists()


class SubscriptionRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='author.email')
    id = serializers.IntegerField(source='author.id')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, object):
        return Subscription.objects.filter(
            user=object.user, author=object.author
        ).exists()

    def get_recipes(self, object):
        recipes_limit = self.context.get('recipes_limit')
        recipes = Recipe.objects.filter(author=object.author)
        if not recipes_limit:
            return SubscriptionRecipeSerializer(recipes, many=True).data
        return SubscriptionRecipeSerializer(
            recipes[:recipes_limit], many=True
        ).data

    def get_recipes_count(self, object):
        return Recipe.objects.filter(author=object.author).count()


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
