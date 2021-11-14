from rest_framework import serializers
from recipes.models import Recipe


class RecipeSerializer(serializers.Serializer):
    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )
