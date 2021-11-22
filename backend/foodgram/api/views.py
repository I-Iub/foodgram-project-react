from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from organizer.models import Favorite, ShoppingCart, Subscription
from recipes.models import Measurement, Recipe, Tag
from users.models import User
from users.permissions import OrganizerOwner, RecipeAuthorOrReadOnly

from .pagination import CustomPagination
from .serializers import (FavoriteSerializer, MeasurementSerializer,
                          RecipeSerializer, SubscriptionSerializer,
                          TagSerializer, UserSerializer)


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

    def get_queryset(self):
        recipe_id = self.kwargs.get('recipe_id')
        favorites = get_object_or_404(Favorite, recipe=recipe_id)
        return favorites


class MeasurementViewSet(viewsets.ModelViewSet):
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    filter_backends = (
        DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter
    )
    filterset_fields = ('name',)
    search_fields = ('^name',)
    ordering_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (RecipeAuthorOrReadOnly,)
    filter_backends = DjangoFilterBackend, filters.OrderingFilter
    filterset_fields = ('tags', 'author')
    ordering_fields = ('name',)

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
        if is_favorited is not None and is_favorited not in ('0', '1'):
            return Response(
                "Ошибка: в параметре запроса 'is_favorited' должен "
                "быть 0 или 1",
                status=status.HTTP_400_BAD_REQUEST
            )
        if is_favorited == '1':
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
                is_in_shopping_cart not in ('0', '1')):
            return Response(
                "Ошибка: в параметре запроса 'is_in_shopping_cart' должен "
                "быть 0 или 1",
                status=status.HTTP_400_BAD_REQUEST
            )
        if is_in_shopping_cart == '1':
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
            # проверяем, что занчение параметра >= 0:
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


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    filter_backends = DjangoFilterBackend, filters.OrderingFilter
    filterset_fields = ('slug',)
    ordering_fields = ('name',)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = DjangoFilterBackend, filters.OrderingFilter
    ordering_fields = ('username', 'first_name', 'last_name')
    ordering = ('first_name',)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()

    # @action(url_path='download_shopping_cart')
    @action(
        methods=['get', 'delete'],
        url_path='shopping-cart',
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
            return Response(
                'Рецепт добавлен в список покупок.',  # не соответствует ТЗ, должен быть json
                status=status.HTTP_201_CREATED
            )
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
