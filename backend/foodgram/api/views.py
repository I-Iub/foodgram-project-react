from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.http import HttpResponse
# from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from organizer.models import Favorite, ShoppingCart, Subscription
from recipes.models import Measurement, Recipe, Tag
from users.models import User
from users.permissions import (OrganizerOwner, RecipeAuthorOrReadOnly,
                               UserPermissions)

from .pagination import CustomPagination
from .serializers import (FavoriteSerializer, MeasurementSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          ShortRecipeSerializer, SubscriptionSerializer,
                          TagSerializer, UserSerializer,
                          UserPasswordSerializer)


def get_integer_list(parameter_list, parameter_name):
    """Возвращает словарь со списком параметров, преобразованных в целые числа
    или ообщением об ошибке, если преобразовать не удалось.
    """
    try:
        integer_list = [
            int(parameter) for parameter in parameter_list
        ]
        return {
            'list': integer_list
        }
    except ValueError:
        return {
            'error_message': f"Ошибка: в параметре запроса '{parameter_name}' "
                             f"должно быть указано натуральное число."
        }


class FavoriteViewSet(viewsets.ModelViewSet):  # переделать!!!
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()

    # def get_queryset(self):
    #     recipe_id = self.kwargs.get('recipe_id')
    #     favorites = get_object_or_404(Favorite, recipe=recipe_id)
    #     return favorites

    @action(
        methods=['get', 'delete'],
        url_path=r'(?P<recipe_id>\d+)/favorite',
        permission_classes=[OrganizerOwner],
        detail=False
    )
    def favorites(self, request, recipe_id):
        user = request.user
        try:  # код ниже повторяет shopping_cart. Нужно декомпозировать и отDRYить______________________
            recipe = Recipe.objects.get(pk=recipe_id)
        except ObjectDoesNotExist:
            return Response(
                {
                    'errors': f'Рецепта с id={recipe_id} не существует.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        is_favorites_exists = Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists()

        if request.method == 'GET' and is_favorites_exists:
            return Response(
                {
                    'errors': 'Этот рецепт уже есть в избранном.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'GET':
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data)

        elif request.method == 'DELETE' and not is_favorites_exists:
            return Response(
                {
                    'errors': 'Ошибка удаления. '
                    'Этого рецепта нет в избранном.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            Favorite.objects.get(user=user, recipe=recipe).delete()
            return Response(
                'Рецепт успешно удалён из избранного.',
                status=status.HTTP_204_NO_CONTENT
            )


class MeasurementViewSet(viewsets.ModelViewSet):
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    filter_backends = (
        DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter
    )
    filterset_fields = ('name',)
    search_fields = ('^name',)
    ordering_fields = ('name',)

    def list(self, request, *args, **kwargs):
        search_parameter = request.query_params.getlist('name')[-1]
        print('search_parameter', search_parameter)
        queryset = Measurement.objects.filter(
            name__istartswith=search_parameter
        )
        print('queryset', queryset)
        serializer = MeasurementSerializer(
            queryset, many=True
        )
        print(serializer.data)
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (RecipeAuthorOrReadOnly,)
    filter_backends = DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter
    filterset_fields = ('tags', 'author')
    ordering_fields = ('name',)
    search_fields = ('ingredients',)

    def list(self, request, *args, **kwargs):
        query_dict = request.query_params  # <QueryDict: {...}>
        queryset = Recipe.objects.all()

        tags_slug_list = query_dict.getlist('tags')  # ['tag_slug1', ...]
        # проверка: в базе данных есть теги с указанным
        # в параметре запроса "tags" слагом
        for tags_slug in tags_slug_list:
            if Tag.objects.filter(slug=tags_slug).exists():
                next
            else:
                return Response(
                    f"Ошибка: в базе данных нет тегов с указанным в параметре "
                    f"запроса слагом {tags_slug}.",
                    status=status.HTTP_400_BAD_REQUEST
                )
        # фильтруем queryset по тегам
        if tags_slug_list:
            queryset = queryset.filter(
                tags__slug__in=tags_slug_list
            ).distinct()  # только уникальные записи

        author_id_list = query_dict.getlist('author')  # [<str>, ...]
        if author_id_list:
            # проверка: указанный в запросе параметр
            # "author" можно преобразовать в int
            data_dictionary = get_integer_list(author_id_list, 'author')
            error_message = data_dictionary.get('error_message')
            if error_message:
                return Response(error_message)
            author_id_integer_list = data_dictionary.get('list')
            # проверяем, что указанные в параметре запроса авторы есть в БД
            for author_id in author_id_integer_list:
                if User.objects.filter(pk=author_id).exists():
                    next
                else:
                    return Response(
                        f"Ошибка: в базе данных нет пользователя с "
                        f"id={author_id}, указанным в параметре запроса "
                        f"'author'.",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            # фильтруем рецепты по авторам
            queryset = queryset.filter(
                author__in=author_id_integer_list
            ).distinct()  # только уникальные записи

        is_favorited = query_dict.get('is_favorited')  # возвращает последний
        if is_favorited is not None and is_favorited not in ('true', 'false'):
            return Response(
                "Ошибка: в параметре запроса 'is_favorited' должно "
                "быть false или true",
                status=status.HTTP_400_BAD_REQUEST
            )
        if is_favorited == 'true':
            recipe_id_list = [
                favorite.recipe.id for favorite in Favorite.objects.filter(
                    user=request.user.id
                    ).only('recipe')
            ]
            queryset = queryset.filter(pk__in=recipe_id_list)

        is_in_shopping_cart = query_dict.get(  # возвращает последний
            'is_in_shopping_cart'
        )
        if (is_in_shopping_cart is not None and
                is_in_shopping_cart not in ('true', 'false')):
            return Response(
                "Ошибка: в параметре запроса 'is_in_shopping_cart' должно "
                "быть true или false",
                status=status.HTTP_400_BAD_REQUEST
            )
        if is_in_shopping_cart == 'true':
            shopping_carts = ShoppingCart.objects.filter(
                user=request.user.id
            ).select_related('recipe')  # .only('recipe') ???
            recipes_list = [cart.recipe for cart in shopping_carts]
            queryset = [
                recipe for recipe in queryset if recipe in recipes_list
            ]

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    pagination_class = CustomPagination
    permission_classes = (OrganizerOwner,)

    # @action(
    #     methods=['get', 'delete'],
    #     url_path=r'(?P<recipe_id>\d+)/subscribe',
    #     permission_classes=[OrganizerOwner],
    #     detail=False
    # )

    def list(self, request):
        recipes_limit = request.query_params.getlist('recipes_limit')

        if recipes_limit:
            # проверка: указанный в запросе параметр
            # "recipes_limit" можно преобразовать в int
            data_dictionary = get_integer_list(recipes_limit, 'recipes_limit')
            error_message = data_dictionary.get('error_message')
            if error_message:
                return Response(error_message)
            # если передано несколько значений, берётся последнее:
            recipes_limit_integer = data_dictionary.get('list')[-1]
            # проверяем, что заначение параметра >= 0:
            if recipes_limit_integer < 0:
                return Response(
                    "Ошибка: в параметре запроса 'recipes_limit' должно быть "
                    "указано целое неотрицательное число",
                    status=status.HTTP_400_BAD_REQUEST
                )

        queryset = Subscription.objects.filter(
            user=request.user.id
        ).select_related('author')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        methods=['get', 'delete'],
        url_path=r'(?P<author_id>\d+)/subscribe',
        permission_classes=[OrganizerOwner],
        detail=False
    )
    def subscribe(self, request, author_id):
        user = request.user

        recipes_limit = request.query_params.get('recipes_limit')
        print()
        print('recipes_limit:', recipes_limit)
        print()
        recipes_limit_integer = get_integer_list(recipes_limit, 'recipes_limit')
        error_message = recipes_limit_integer.get('error_message')
        if error_message:
            return Response(error_message)

        # author_id_integer = get_integer_list(author_id, 'author_id')
        # print(author_id_integer)
        # error_message = author_id_integer.get('error_message')
        # print(error_message)
        # if error_message:
        #     return Response(error_message)

        if user.id == int(author_id):
            return Response(
                {
                    'errors': 'Нельзя подписаться на самого себя.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:  # код ниже повторяет shopping_cart. Нужно декомпозировать и отDRYить______________________
            author = User.objects.get(pk=author_id)
        except ObjectDoesNotExist:
            return Response(
                {
                    'errors': f'Пользователя с id={author_id} не существует.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        is_subscription_exists = Subscription.objects.filter(
            user=user, author=author
        ).exists()

        if request.method == 'GET' and is_subscription_exists:
            return Response(
                {
                    'errors': 'Вы уже подписаны на этого автора.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'GET':
            subscription = Subscription.objects.create(
                user=user, author=author
            )
            serializer = SubscriptionSerializer(subscription, context={'request': request})
            return Response(serializer.data)

        elif request.method == 'DELETE' and not is_subscription_exists:
            return Response(
                {
                    'errors': 'Ошибка удаления. '
                    'Нет подписки на этого автора.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            Subscription.objects.get(user=user, author=author).delete()
            return Response(
                'Подписка успешно удалёна.',
                status=status.HTTP_204_NO_CONTENT
            )

        # return Response(f'1111111111111111111 {recipes_limit}')


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    filter_backends = DjangoFilterBackend, filters.OrderingFilter
    filterset_fields = ('slug',)
    ordering_fields = ('name',)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserPermissions]
    filter_backends = DjangoFilterBackend, filters.OrderingFilter
    ordering_fields = ('username', 'first_name', 'last_name')
    ordering = ('first_name',)

    # def create(self, request):
    #     return Response({'message': 'created!'})

    @action(
        methods=['get'],
        url_path='me',
        permission_classes=[UserPermissions],
        detail=False  # Почему не работает с detail=True ???======================
    )
    def get_me(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(
                {
                        "detail": "Учетные данные не были предоставлены."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        user_data = User.objects.get(pk=user.id)
        serializer = UserSerializer(user_data, context={'request': request})
        return Response(serializer.data)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer

    @action(
        methods=['get', 'delete'],
        url_path=r'(?P<recipe_id>\d+)/shopping_cart',
        permission_classes=[OrganizerOwner],
        detail=False
    )
    def shopping_cart(self, request, recipe_id):
        user = request.user
        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except ObjectDoesNotExist:
            return Response(
                {
                    'errors': f'Рецепта с id={recipe_id} не существует.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        is_shopping_cart_exists = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists()

        if request.method == 'GET' and is_shopping_cart_exists:
            return Response(
                {
                    'errors': 'Этот рецепт уже есть в списке покупок.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'GET':
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data)
            # return Response(
            #     'Рецепт добавлен в список покупок.',  # не соответствует ТЗ, должен быть json
            #     status=status.HTTP_201_CREATED
            # )

        elif request.method == 'DELETE' and not is_shopping_cart_exists:
            return Response(
                {
                    'errors': 'Ошибка удаления. '
                    'Этого рецепта нет в списке покупок.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            ShoppingCart.objects.get(user=user, recipe=recipe).delete()
            return Response(
                'Рецепт успешно удалён из списка покупок.',
                status=status.HTTP_204_NO_CONTENT
            )


@api_view(['GET'])
# permission_classes([OrganizerOwner])  # ????????????????????????????????????????
def download_shopping_cart(request):
    user = request.user

    recipes = Recipe.objects.filter(
        shopping_cart_of_recipe__user__exact=user
    ).prefetch_related('ingredients__measurement')
    querysets = [recipe.ingredients.all() for recipe in recipes]

    ingredients_total = []
    for queryset in querysets:
        ingredients = [ingredient for ingredient in queryset]
        ingredients_total += ingredients

    shopping_list = {}
    for ingredient in ingredients_total:
        key = (f'{ingredient.measurement.name} '
               f'({ingredient.measurement.measurement_unit})')
        shopping_list[key] = (
            shopping_list.get((key), 0) + ingredient.amount
        )
    data = '\n'.join(
        [f'{name}\t{amount}' for name, amount in shopping_list.items()]
    )

    file_name = f'{user.username}_shopping_cart.txt'
    file_path = f'{settings.MEDIA_ROOT}/shopping_carts/{file_name}'
    with open(file_path, 'w') as file_object:  # возможно ли сделать без сохранения в файловой системе?
        file = File(file_object)
        file.write(data)  # добавить обработку ошибок ввода/вывода (exception)

    response = HttpResponse(open(file_path), content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={file_name}'
    return response


@api_view(['POST'])
def set_password(request):
    serializer = UserPasswordSerializer(
        data=request.data, context=request
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    User.objects.filter(pk=request.user.id).update(
        password=make_password(request.data.get('new_password'))
    )
    return Response('Пароль успешно изменён.')  # ????????????????????????????????????
