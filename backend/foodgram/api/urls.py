from django.urls import include, path
from rest_framework import routers

from .views import (FavoriteViewSet, MeasurementViewSet, RecipeViewSet,
                    ShoppingCartViewSet, SubscriptionViewSet, TagViewSet,
                    UserViewSet, download_shopping_cart)

router = routers.DefaultRouter()
# router.register(
#     'recipes',
#     ShoppingCartDownloadViewSet,
#     basename='download_shopping_cart'
# )

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('recipes', FavoriteViewSet, basename='favorites')
router.register('recipes', ShoppingCartViewSet, basename='shopping_cart')
router.register('tags', TagViewSet, basename='tags')
router.register(
    'users/subscriptions', SubscriptionViewSet, basename='subscriptions'
)
router.register('users', UserViewSet, basename='users')

router.register('ingredients', MeasurementViewSet, basename='ingredients')

urlpatterns = [
    path('recipes/download_shopping_cart/', download_shopping_cart),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
