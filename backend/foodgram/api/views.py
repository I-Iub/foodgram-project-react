from io import StringIO
from wsgiref.util import FileWrapper

from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.serializers import (FavoriteSerializer, MeasurementSerializer,
                             RecipeSerializer, ShoppingCartSerializer,
                             ShortRecipeSerializer, SubscriptionSerializer,
                             TagSerializer, UserPasswordSerializer,
                             UserSerializer)
from api.utils import get_integer_list, get_object_if_exists
from organizer.models import Favorite, ShoppingCart, Subscription
from recipes.models import Ingredient, Measurement, Recipe, Tag
from users.models import User
from users.permissions import (OrganizerOwner, RecipeAuthorOrReadOnly,
                               UserPermissions)

RECIPES_LIMIT_ERROR_MESSAGE = ("Ошибка: в параметре запроса 'recipes_limit' "
                               "должно быть указано целое неотрицательное "
                               "число.")
UNKNOWN_REQUEST = {'errors': 'Неизвестный или неразрешенный запрос.'}


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()

    @action(
        methods=['get', 'delete'],
        url_path=r'(?P<recipe_id>\d+)/favorite',
        permission_classes=[OrganizerOwner],
        detail=False
    )
    def favorites(self, request, recipe_id):
        user = request.user

        recipe = get_object_if_exists(Recipe, recipe_id)
        error_message = recipe.get('error_message')
        if error_message:
            return Response(error_message, status=status.HTTP_404_NOT_FOUND)
        recipe = recipe.get('object')

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
        else:
            return Response(
                UNKNOWN_REQUEST,
                status=status.HTTP_400_BAD_REQUEST
            )


class MeasurementViewSet(viewsets.ModelViewSet):
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    filter_backends = (
        IngredientFilter, filters.OrderingFilter
    )
    search_fields = ('^name',)
    ordering_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    permission_classes = (RecipeAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,
                       filters.SearchFilter)
    filter_class = RecipeFilter
    filterset_fields = ('tags', 'author')
    ordering_fields = ('name',)
    search_fields = ('ingredients',)

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
        context = super().get_serializer_context()
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
                    RECIPES_LIMIT_ERROR_MESSAGE,
                    status=status.HTTP_400_BAD_REQUEST
                )
            # передаём обработанный параметр recipes_limit в context
            context['recipes_limit'] = recipes_limit_integer

        queryset = Subscription.objects.filter(
            user=request.user.id
        ).select_related('author')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, context=context, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, context=context, many=True)
        return Response(serializer.data)

    @action(
        methods=['get', 'delete'],
        url_path=r'(?P<author_id>\d+)/subscribe',
        permission_classes=[OrganizerOwner],
        detail=False
    )
    def subscribe(self, request, author_id):
        user = request.user

        context = super().get_serializer_context()

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
                    RECIPES_LIMIT_ERROR_MESSAGE,
                    status=status.HTTP_400_BAD_REQUEST
                )
            # передаём обработанный параметр recipes_limit в context
            context['recipes_limit'] = recipes_limit_integer

        if user.id == int(author_id):
            return Response(
                {
                    'errors': 'Нельзя подписаться на самого себя.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        author = get_object_if_exists(User, author_id)
        error_message = author.get('error_message')
        if error_message:
            return Response(error_message, status=status.HTTP_404_NOT_FOUND)
        author = author.get('object')

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
            serializer = SubscriptionSerializer(
                subscription, context=context
            )
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
        else:
            return Response(
                UNKNOWN_REQUEST,
                status=status.HTTP_400_BAD_REQUEST
            )


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

    @action(
        methods=['get'],
        url_path='me',
        permission_classes=[IsAuthenticated],
        detail=False
    )
    def get_me(self, request):
        user = request.user
        user_data = get_object_or_404(User, pk=user.id)
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
        except Recipe.DoesNotExist:
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
        else:
            return Response(
                UNKNOWN_REQUEST,
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([OrganizerOwner])
def download_shopping_cart(request):
    user = request.user

    ingredients = Ingredient.objects.filter(
        recipes__shopping_cart__user=user
    ).values(
        'measurement__name', 'measurement__measurement_unit'
    ).annotate(amount=Sum('amount'))
    ingredient_list = []
    for ingredient in ingredients:
        normalized = ingredient.get('amount').normalize()
        sign, digit, exponent = normalized.as_tuple()
        if exponent <= 0:
            amount = normalized
        else:
            amount = normalized.quantize(1)

        ingredient_list.append(
            f"{ingredient.get('measurement__name')} "
            f"({ingredient.get('measurement__measurement_unit')})"
            f"\t{amount}"
        )
    data = '\n'.join(ingredient_list)
    file_name = f'{user.username}_shopping_cart.txt'
    file = StringIO(data)
    response = HttpResponse(FileWrapper(file), content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={file_name}'

    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_password(request):
    serializer = UserPasswordSerializer(
        data=request.data, context=request
    )
    serializer.is_valid(raise_exception=True)
    User.objects.filter(pk=request.user.id).update(
        password=make_password(request.data.get('new_password'))
    )
    return Response('Пароль успешно изменён.')
