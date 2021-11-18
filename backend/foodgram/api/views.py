from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status, viewsets
from rest_framework.response import Response

from organizer.models import Favorite, Subscription
from recipes.models import Measurement, Recipe, Tag
from users.models import User
from users.permissions import OrganizerOwner, RecipeAuthorOrReadOnly

from .serializers import (FavoriteSerializer, MeasurementSerializer,
                          RecipeSerializer, SubscriptionSerializer,
                          TagSerializer, UserSerializer)


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


class AuthorIdException(Exception):
    """В параметре запроса "author" должно быть указано натуральное число"""


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (RecipeAuthorOrReadOnly,)
    filter_backends = DjangoFilterBackend, filters.OrderingFilter
    filterset_fields = ('tags', 'author')
    ordering_fields = ('name',)

    def list(self, request):
        query_dict = request.query_params  # <QueryDict: {}>
        queryset = Recipe.objects.all()

        # проверка: в базе данных есть теги с указанным
        # в параметре запроса "tags" слагом
        tags_slug_list = query_dict.getlist('tags')  # ['tag_slug1', ...]
        for tags_slug in tags_slug_list:
            if Tag.objects.filter(slug=tags_slug).exists():
                next
            else:
                return Response(
                    "Ошибка: в базе данных нет тегов с указанным в параметре "
                    "запроса 'tags' слагом",
                    status=status.HTTP_400_BAD_REQUEST
                )
        # фильтруем queryset по тегам
        if tags_slug_list:
            queryset = queryset.filter(
                tags__slug__in=tags_slug_list
            ).distinct()  # только уникальные записи

        # проверка: указанный в запросе параметр
        # "author" можно преобразовать в int
        author_id_list = query_dict.getlist('author')  # <str>
        if author_id_list:
            try:
                author_id_int = [  # [<int>, ...]
                    int(author_id_str) for author_id_str in author_id_list
                ]
            except ValueError:
                return Response(
                    "Ошибка: в параметре запроса 'author' должно быть указано "
                    "натуральное число",
                    status=status.HTTP_400_BAD_REQUEST
                )
        # проверяем, что указанные в параметре запроса авторы есть в БД
        for author in author_id_list:
            if User.objects.filter(pk=int(author)).exists():
                next
            else:
                return Response(
                    "Ошибка: в базе данных нет пользователей с id, указанным "
                    "в параметре запроса 'author'",
                    status=status.HTTP_400_BAD_REQUEST
                )
        # фильтруем по авторам
        if author_id_list:
            queryset = queryset.filter(
                author__in=author_id_int
            ).distinct()  # только уникальные записи

        # print(query_dict)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (OrganizerOwner,)


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
