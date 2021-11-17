from base64 import b64decode
from datetime import timedelta

from rest_framework import serializers
from django.core.files.base import ContentFile

from organizer.models import Favorite, Subscription
from recipes.models import Ingredient, Measurement, Recipe, Tag
# from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = ('name', 'measurement_unit')


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_measurement_unit(self, object):
        return object.measurement.measurement_unit

    def get_name(self, object):
        return object.measurement.name


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Subscription
        fields = ('id', 'user', 'author')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',)


class Base64ToImageField(serializers.ImageField):
    def to_internal_value(self, base64_string):
        # encoded_string = base64_string.encode('utf-8')
        if not base64_string:
            return super().to_internal_value(None)  # ??? Проверить как будет работать!!!!!!!!!!!!!!!
        if base64_string.startswith('data:image'):
            description, image_string = base64_string.split(';base64,')  # format ~= data:image/X,
            extension = description.split('/')[-1]  # разрешение файла
            data = ContentFile(
                b64decode(image_string), name='temp.' + extension
            )
        else:
            image_string = base64_string
            data = ContentFile(b64decode(image_string), name='temp.jpeg')
        return super().to_internal_value(data)
        # return data

    # def to_internal_value(self, base64_string):
    #     # base64_string = base64_string.split(',', maxsplit=1)[1]
    #     encoded_string = base64_string.encode('utf-8')
    #     return decodebytes(encoded_string)

    # def to_representation():
    #     pass


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  # required=False ????????????????????????????????????????????
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientSerializer(many=True)
    # image = Base64ToImageField(read_only=True)
    image = Base64ToImageField()
    cooking_time = serializers.DurationField(read_only=True)
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

    # def validate_tags(self, value):
    #     print('VALUE', value)
    #     # if not value:
    #     #     raise serializers.ValidationError('Должен быть указан тэг(и)')
    #     return value

    def create(self, validated_data):
        validated_data.pop('ingredients')  # ингредиенты обрабатываются ниже
        # создаём копию validated_data, чтобы не изменять исходные данные:
        validated_data_popped = validated_data.copy()
        # удаляем кортинку (<ContentFile>), т.к. эти данные меняются:
        validated_data_popped.pop('image')

        # print('validated_data_popped', validated_data_popped)
        # print(Recipe.objects.filter(**validated_data_popped).exists())

        # Проверка наличия в базе Рецепта, похожего на сохраняемый
        if Recipe.objects.filter(**validated_data_popped).exists():
            raise serializers.ValidationError('У вас уже есть такой рецепт')

        tag_list = self.initial_data.get('tags')
        if tag_list:
            tags_objects = [Tag.objects.get(id=tag_id) for tag_id in tag_list]
        else:
            raise serializers.ValidationError('Не указаны теги')

        ingredients_list = []
        if 'ingredients' not in self.initial_data:
            raise serializers.ValidationError('Не указаны ингредиенты')
        # initial_ingredients_list: [{'id': <int>, 'amount': <int>},]
        initial_ingredients_list = self.initial_data.get('ingredients')
        for ingredient_dict in initial_ingredients_list:
            measurement_id = ingredient_dict.get('id')  # <int>
            measurement_object = Measurement.objects.get(id=measurement_id)
            amount = ingredient_dict.get('amount')  # <int>
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
            ingredients_list += [ingredient_object]
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_objects)
        recipe.ingredients.set(ingredients_list)
        recipe.cooking_time = timedelta(
            minutes=self.initial_data.get('cooking_time')
        )
        return recipe

    def get_is_favorited(self, object):
        return object.favorites.exists()

    def get_is_in_shopping_cart(self, object):
        return object.shopping_cart.exists()
