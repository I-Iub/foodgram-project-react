from base64 import b64decode
from datetime import timedelta

from rest_framework import serializers
from django.core.files.base import ContentFile

from organizer.models import Favorite, ShoppingCart, Subscription
from recipes.models import Ingredient, Measurement, Recipe, Tag
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


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, object):
        return object.subscriptions.exists()


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


# def recipe_tags_validate(self, value):
#     print(self.context['request'].method)

#     # raise serializers.ValidationError('В базе данных отсутствует тег с указанным слагом')
#     return value


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  # required=False ????????????????????????????????????????????
    # tags = TagSerializer(many=True, read_only=True, validators=[recipe_tags_validate])
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
        # validators = [  # не нужен в случае с ModelSerializer, т.к. прописан в модели
        #     UniqueTogetherValidator(
        #         queryset=Recipe.objects.all(),
        #         fields=('author', 'name', 'text', 'cooking_time'),
        #         message='UniqueTogetherValidator: У вас уже есть такой рецепт'
        #     )
        # ]

    # def validate_tags(self, value):
    #     print('VALUE', value)
    #     # if not value:
    #     #     raise serializers.ValidationError('Должен быть указан тэг(и)')
    #     return value

    def create(self, validated_data):
        validated_data.pop('ingredients')  # ингредиенты обрабатываются ниже
        # создаём копию validated_data, чтобы не изменять исходные данные:
        validated_data_poped = validated_data.copy()
        # удаляем кортинку (<ContentFile>), т.к. эти данные меняются:
        validated_data_poped.pop('image')

        # print('validated_data_poped', validated_data_poped)
        # print(Recipe.objects.filter(**validated_data_poped).exists())

        # Проверка наличия в базе Рецепта, похожего на сохраняемый
        if Recipe.objects.filter(**validated_data_poped).exists():
            raise serializers.ValidationError('У вас уже есть такой рецепт')

        tag_list = self.initial_data.get('tags')  # здесь и везде добавить валидацию initial_data
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

    def update(self, instance, validated_data):
        # print(validated_data) --> {
        #     'ingredients': [OrderedDict([('amount', Decimal('10.000'))]), OrderedDict([('amount', Decimal('30.000'))])],
        #     'name': 'from api. image: duck',
        #     'image': <ContentFile: Raw content>,
        #     'text': '907'
        # }

        # print(self.initial_data)
        # {
        #     'ingredients':
        #         [
        #             {'id': 1201, 'amount': 10},
        #             {'id': 120, 'amount': 30}
        #         ],
        #     'tags':
        #         [
        #             1,
        #             2
        #         ],
        #     'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==',
        #     'name': 'from api. image: duck 907',
        #     'text': '907',
        #     'cooking_time': 12
        # }

        # print(instance)  # Recipe
        # print(self.data)
        # tag_id = [tag_id.get('id') for tag_id in self.data.get('tags')]
        # print(*tag_id)
        # print(self.context.get('request'))

        # блок кода ниже повторяет код в create.
        tag_list = self.initial_data.get('tags')  # здесь и везде добавить валидацию initial_data
        if tag_list:
            tags_objects = [Tag.objects.get(id=tag_id) for tag_id in tag_list]
        # else:
        #     raise serializers.ValidationError('Не указаны теги')

            instance.tags.set(tags_objects)

        ingredients_list = []  # блок кода ниже повторяет код в create. Сделать валидацию полученных значений?
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

        if ingredients_list:
            instance.ingredients.set(ingredients_list)

        cooking_time = self.initial_data.get('cooking_time')
        if cooking_time:
            instance.cooking_time = timedelta(
                minutes=cooking_time
            )

        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)

        return instance

    def get_is_favorited(self, object):
        return object.favorites.exists()

    def get_is_in_shopping_cart(self, object):
        return object.shopping_cart_of_recipe.exists()

    # def to_representation(self, object):
    #     return {
    #         'name': object.name,
    #         'message': 'Fuck you Spielberg!'
    #     }


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

    class Meta:
        model = Subscription
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes'
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
            user=object.author, author=object.user
        ).exists()
        return is_subscribed

    def get_recipes(self, object):
        print(self.context.get('request').query_params.get('recipes_limit'))
        request = self.context.get('request')
        recipes_limit = int(request.query_params.get('recipes_limit'))
        recipes = Recipe.objects.filter(author=object.author)[:recipes_limit]
        return SubscriptionRecipeSerializer(recipes, many=True).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
