from django.contrib import admin

from .models import Ingredient, Measurement, Recipe, Tag


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'measurement_unit', 'amount')
    search_fields = ('measurement_unit',)
    list_filter = ('measurement_unit',)
    empty_value_display = '-пусто-'


class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measure')
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
