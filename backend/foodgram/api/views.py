from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, viewsets
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


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (RecipeAuthorOrReadOnly,)
    filter_backends = DjangoFilterBackend, filters.OrderingFilter
    filterset_fields = ('tags', 'author')
    ordering_fields = ('name',)

    def list(self, request):
        # необходимо валидировать слаг, который пришел с запросом и проверить что они есть в базе
        # print()
        # print('GET!!!')
        # # print(request.query_params.getlist('tags'))
        # print(request.GET)
        query_dict = request.query_params  # <QueryDict: {}>
        tags_slug_list = query_dict.getlist('tags')  # ['tag_slug1', ...]
        # if tags_slug_list:
        #     tags = Tag.objects.filter(slug__in=tags_slug_list)
        #     tag_id_list = ['tags=' + str(tag.id) for tag in tags]
        #     print(tag_id_list)
        #     query_string = '&'.join(tag_id_list)
        #     print(query_string)
        #     print(type(query_string))
        #     # # QueryDict(query_string)
        #     # print(QueryDict(query_string))
        #     # request.query_params = QueryDict(query_string)
        for tags_slug in tags_slug_list:
            if Tag.objects.filter(slug=tags_slug).exists():
                print('exists')
                next
            else:
                raise serializers.ValidationError(
                    f"Тега со слагом '{tags_slug}' нет в базе данных"
                )

        queryset = Recipe.objects.filter(tags__slug__in=tags_slug_list)
        # print(test_queryset)
        # print(test_queryset.count())

        # queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # def get_queryset(self):
    #     # print(self.request.query_params.getlist('tags'))
    #     tags = self.request.query_params.getlist('tags')
    #     # author = self.request.query_params.getlist('author')
    #     # print()
    #     # print(tags)
    #     # print()
    #     if tags:
    #         tags_queryset = Tag.objects.filter(slug__in=tags)
    #         # print(tags_queryset)
    #         # print()
    #         tag_id_list = []
    #         for tag in tags_queryset:
    #             tag_id_list += [tag.id]
    #         queryset = Recipe.objects.filter(tags__in=tag_id_list)
    #         # print(queryset)
    #         # print()
    #     return Recipe.objects.all()

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
