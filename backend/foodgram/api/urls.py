from django.urls import include, path
from rest_framework import routers

from .views import (FavoriteViewSet, MeasurementViewSet, RecipeViewSet,
                    ShoppingCartViewSet, SubscriptionViewSet, TagViewSet,
                    UserViewSet)

router = routers.DefaultRouter()
# router.register(
#     'recipes',
#     ShoppingCartDownloadViewSet,
#     basename='download_shopping_cart'
# )
router.register(
    r'recipes/(?P<recipe_id>\d+)/favorites',
    FavoriteViewSet,
    basename='favorites'
)
router.register('recipes', ShoppingCartViewSet, basename='shopping_cart')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register(
    'users/subscriptions', SubscriptionViewSet, basename='subscriptions'
)
router.register('users', UserViewSet, basename='users')

router.register('ingredients', MeasurementViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
