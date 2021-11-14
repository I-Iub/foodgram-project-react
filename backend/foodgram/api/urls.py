from django.urls import include, path
from rest_framework import routers

from .views import RecipeViewSet, TagViewSet

v1 = routers.DefaultRouter()
v1.register('recipes', RecipeViewSet, basename='recipes')
v1.register('tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
