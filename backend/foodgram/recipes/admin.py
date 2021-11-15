from django.contrib import admin

from .models import Ingredient, Measurement, Recipe, Tag


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'measurement', 'amount')
    search_fields = ('measurement',)
    list_filter = ('measurement',)
    empty_value_display = '-пусто-'


class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'name', 'text', 'cooking_time')
    search_fields = (
        'tags',
        'author',
        'ingredients',
        'name',
        'text',
        'cooking_time'
    )
    list_filter = (
        'tags',
        'author',
        'ingredients',
        'name',
        'text',
        'cooking_time'
    )
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')
    empty_value_display = '-пусто-'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Measurement, MeasurementAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
