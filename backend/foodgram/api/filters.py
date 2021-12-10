from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filters_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filters_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def filters_is_favorited(self, queryset, name, value):
        print(value)
        print(queryset.filter(favorites__user=self.request.user))
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filters_is_in_shopping_cart(self, queryset, name, value):
        print(value)
        print(queryset.filter(shopping_cart__user=self.request.user))
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
