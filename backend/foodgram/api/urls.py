from django.urls import include, path
from rest_framework import routers

from .views import (MeasurementViewSet, RecipeViewSet, SubscriptionViewSet,
                    TagViewSet, UserViewSet)

v1 = routers.DefaultRouter()
v1.register('recipes', RecipeViewSet, basename='recipes')
v1.register('tags', TagViewSet, basename='tags')
v1.register('users', UserViewSet, basename='users')
v1.register(
    'users/subscriptions', SubscriptionViewSet, basename='subscriptions'
)
v1.register('ingredients', MeasurementViewSet, basename='ingredients')

urlpatterns = [
    path('', include(v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
