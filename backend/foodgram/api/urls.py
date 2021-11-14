from django.urls import include, path
from rest_framework import routers

from .views import RecipeViewSet

v1 = routers.DefaultRouter()
v1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(v1.urls)),
]
