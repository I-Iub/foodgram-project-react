from django.urls import include, path
from rest_framework import routers

from .views import (FavoriteViewSet, MeasurementViewSet, RecipeViewSet,
                    ShoppingCartViewSet, SubscriptionViewSet, TagViewSet,
                    UserViewSet, download_shopping_cart, set_password)

router = routers.DefaultRouter()

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('recipes', FavoriteViewSet, basename='favorite')
router.register('recipes', ShoppingCartViewSet, basename='shopping_cart')
router.register('tags', TagViewSet, basename='tags')
router.register('users', UserViewSet, basename='users')
router.register('users', SubscriptionViewSet, basename='subscriptions')

router.register('ingredients', MeasurementViewSet, basename='ingredients')

urlpatterns = [
    path('recipes/download_shopping_cart/', download_shopping_cart),
    path('users/subscriptions/', SubscriptionViewSet.as_view({'get': 'list'})),
    path('users/set_password/', set_password),
    path('', include(router.urls)),
]
