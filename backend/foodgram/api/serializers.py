from base64 import b64decode

from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from organizer.models import Favorite, ShoppingCart, Subscription
from recipes.models import Ingredient, Measurement, Recipe, Tag
from rest_framework import serializers
from users.models import User


def get_tags_objects(tag_list):
    try:
        tags_objects = [
            Tag.objects.get(id=tag_id) for tag_id in tag_list
        ]
    except ObjectDoesNotExist:
        raise serializers.ValidationError({
            'tags': ['Тега не существует.']
        })
    return tags_objects


def get_ingredients_objects(initial_ingredients_list):
    ingredients_objects = []
    for ingredient_dict in initial_ingredients_list:
        measurement_id = ingredient_dict.get('id')
        try:
            measurement_object = Measurement.objects.get(id=measurement_id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError({
                'ingredients': [
                    'Ингредиента не существует.'
                ]
            })
        amount = ingredient_dict.get('amount')
        try:
            amount = float(amount)
        except ValueError:
            raise serializers.ValidationError({
                'amount': [
                    'Количество ингредиента укажите числом с точкой в '
                    'качестве разделителя десятичной части.'
                ]
            })
        except TypeError:
            raise serializers.ValidationError({
                'amount': [
                    'Количество ингредиента укажите числом с точкой в '
                    'качестве разделителя десятичной части.'
                ]
            })
        if not Ingredient.objects.filter(
                                            measurement=measurement_object,
                                            amount=amount).exists():
            ingredient_object = Ingredient.objects.create(
                measurement=measurement_object,
                amount=amount
            )
        else:
            ingredient_object = Ingredient.objects.get(
                measurement=measurement_object,
                amount=amount
            )
        ingredients_objects += [ingredient_object]
    return ingredients_objects


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = ('id', 'name', 'measurement_unit')


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_measurement_unit(self, object):
        return object.measurement.measurement_unit

    def get_name(self, object):
        return object.measurement.name

    def get_amount(self, object):
        return object.amount.normalize()

    def get_id(self, object):
        return object.measurement.id


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
        return super(UserSerializer, self).create(validated_data)

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
        user = User.objects.get(pk=self.context.user.id)
        if not user.check_password(value):
            raise serializers.ValidationError()
        return value


class Base64ToImageField(serializers.ImageField):
    def to_internal_value(self, base64_string):
        if not base64_string:
            return super().to_internal_value(None)
        if base64_string.startswith('data:image'):
            description, image_string = base64_string.split(';base64,')
            extension = description.split('/')[-1]  # разрешение файла
            data = ContentFile(
                b64decode(image_string), name='temp.' + extension
            )
        else:
            image_string = base64_string
            data = ContentFile(b64decode(image_string), name='temp.jpeg')
        return super().to_internal_value(data)


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
    tags = TagSerializer(many=True, read_only=True)
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

    def create(self, validated_data):
        validated_data.pop('ingredients')  # ингредиенты обрабатываются ниже
        # создаём копию validated_data, чтобы не изменять исходные данные:
        validated_data_poped = validated_data.copy()
        # удаляем кортинку (<ContentFile>), т.к. эти данные меняются:
        validated_data_poped.pop('image')
        # Проверка наличия в базе Рецепта, похожего на сохраняемый
        if Recipe.objects.filter(**validated_data_poped).exists():
            raise serializers.ValidationError('У вас уже есть такой рецепт')

        tag_list = self.initial_data.get('tags')
        if tag_list:
            tags_objects = get_tags_objects(tag_list)
        else:
            raise serializers.ValidationError({
                'tags': ['Обязательное поле.']
            })

        initial_ingredients_list = self.initial_data.get('ingredients')
        ingredients_objects = get_ingredients_objects(initial_ingredients_list)

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_objects)
        recipe.ingredients.set(ingredients_objects)

        return recipe

    def update(self, instance, validated_data):
        tag_list = self.initial_data.get('tags')
        if tag_list:
            tags_objects = get_tags_objects(tag_list)
            instance.tags.set(tags_objects)
        else:
            raise serializers.ValidationError({
                'tags': ['Обязательное поле.']
            })

        initial_ingredients_list = self.initial_data.get('ingredients')
        ingredients_objects = get_ingredients_objects(initial_ingredients_list)

        if ingredients_objects:
            instance.ingredients.set(ingredients_objects)

        cooking_time = self.initial_data.get('cooking_time')
        if cooking_time:
            instance.cooking_time = cooking_time

        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)

        instance.save()
        return instance

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
    email = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
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

    def get_email(self, object):
        return object.author.email

    def get_id(self, object):
        return object.author.id

    def get_username(self, object):
        return object.author.username

    def get_first_name(self, object):
        return object.author.first_name

    def get_last_name(self, object):
        return object.author.last_name

    def get_is_subscribed(self, object):
        is_subscribed = Subscription.objects.filter(
            user=object.user, author=object.author
        ).exists()
        return is_subscribed

    def get_recipes(self, object):
        request = self.context.get('request')
        if not request.query_params.get('recipes_limit'):
            recipes = Recipe.objects.filter(author=object.author)
            return SubscriptionRecipeSerializer(recipes, many=True).data
        recipes_limit = int(request.query_params.get('recipes_limit'))
        recipes = Recipe.objects.filter(author=object.author)[:recipes_limit]
        return SubscriptionRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, object):
        recipes_count = Recipe.objects.filter(author=object.author).count()
        return recipes_count


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
