from django.shortcuts import get_object_or_404
from rest_framework import viewsets

from organizer.models import Favorite, Subscription
from recipes.models import Measurement, Recipe, Tag
from users.models import User
from users.permissions import OrganizerOwner, RecipeAuthorOrReadOnly

from .serializers import (FavoriteSerializer, MeasurementSerializer, RecipeSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserSerializer)


class FavoriteViewSet(viewsets.ModelViewSet):  # переделать!!!
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        recipe_id = self.kwargs.get('recipe_id')
        favorites = get_object_or_404(Favorite, recipe=recipe_id)
        return favorites


class MeasurementViewSet(viewsets.ModelViewSet):
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (RecipeAuthorOrReadOnly,)


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (OrganizerOwner,)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
