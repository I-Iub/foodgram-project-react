from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from organizer.models import Favorite, ShoppingCart, Subscription
from recipes.models import Ingredient, Measurement, Recipe, Tag
from rest_framework import serializers
from users.models import User

from .fields import Base64ToImageField
from .utils import (check_id_list, check_ingredients_data,
                    get_ingredients_objects)

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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


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
        try:
            validate_password(value)
        except serializers.ValidationError as error:
            raise serializers.ValidationError(str(error))
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
        try:
            validate_password(value)
        except serializers.ValidationError as error:
            raise serializers.ValidationError(str(error))
        return value

    def validate_current_password(self, value):
        user = get_object_or_404(User, pk=self.context.user.id)  # посмотреть где ещё применить в проекте get_object_or_404
        if not user.check_password(value):
            raise serializers.ValidationError({
                'current_password': 'Текущий пароль неверный.'
            })
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
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientSerializer(read_only=True, many=True)
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

    def validate(self, data):
        errors = {}

        tag_list = self.initial_data.get('tags')
        if not tag_list:
            errors['tags'] = [REQUIRED_FIELD]
        else:
            tag_errors = check_id_list(Tag, tag_list)
            if tag_errors:
                errors['tags'] = tag_errors

        initial_ingredients_list = self.initial_data.get('ingredients')  # использовать data????
        if not initial_ingredients_list:
            errors['ingredients'] = [REQUIRED_FIELD]
        else:
            ingredients_errors = check_ingredients_data(
                initial_ingredients_list
            )
            if ingredients_errors:
                errors['ingredients'] = ingredients_errors
        # if not initial_ingredients_list:
        #     errors['ingredients'] = [REQUIRED_FIELD]
        # else:
        #     measurement_list = []
        #     amount_list = []
        #     for ingredient in initial_ingredients_list:
        #         measurement_list.append(ingredient.get('id'))
        #         amount_list.append(ingredient.get('amount'))

        #     measurement_errors = check_id_list(Measurement, measurement_list)
        #     amount_errors = check_amount_list(amount_list)
        #     if measurement_errors or amount_errors:
        #         errors['ingredients'] = {}
        #     if measurement_errors:
        #         errors['ingredients']['id'] = measurement_errors
        #     if amount_errors:
        #         errors['ingredients']['amount'] = amount_errors

        if errors:
            raise serializers.ValidationError(errors)

        # создаём копию data, чтобы не изменять исходные данные:
        data_poped = data.copy()
        # удаляем кортинку (<ContentFile>), т.к. эти данные меняются:
        if 'image' in data:
            data_poped.pop('image')
        # Проверка наличия в базе Рецепта, похожего на сохраняемый
        if Recipe.objects.filter(**data_poped).exists():
            raise serializers.ValidationError({
                'errors': 'У вас уже есть такой рецепт'
            })

        data['tags'] = list(set(tag_list))
        data['ingredients'] = initial_ingredients_list
        return data

    def create(self, validated_data):
        tag_list = validated_data.pop('tags')
        if tag_list:
            tags_objects = [
                get_object_or_404(Tag, pk=tag_id) for tag_id in tag_list
            ]

        initial_ingredients_list = validated_data.pop('ingredients')
        ingredients_objects = get_ingredients_objects(initial_ingredients_list)

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

        initial_ingredients_list = validated_data.pop('ingredients')
        ingredients_objects = get_ingredients_objects(initial_ingredients_list)
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
        request = self.context.get('request')
        if not request.query_params.get('recipes_limit'):
            recipes = Recipe.objects.filter(author=object.author)
            return SubscriptionRecipeSerializer(recipes, many=True).data
        recipes_limit = int(request.query_params.get('recipes_limit'))
        recipes = Recipe.objects.filter(author=object.author)[:recipes_limit]
        return SubscriptionRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, object):
        return Recipe.objects.filter(author=object.author).count()


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
