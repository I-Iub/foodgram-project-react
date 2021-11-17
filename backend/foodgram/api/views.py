from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

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
    filterset_fields = ('tags',)
    ordering_fields = ('name',)

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
    filter_backends = filters.OrderingFilter
    ordering_fields = ('name',)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = filters.OrderingFilter
    ordering_fields = ('username', 'first_name', 'last_name')
    ordering = ('first_name',)
