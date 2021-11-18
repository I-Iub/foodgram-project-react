from datetime import timedelta

from django.db import models
from users.models import User

RECIPE_MIN_COOKING_TIME = timedelta(minutes=1)
INGREDIENT_MIN_AMOUNT = 0


class Recipe(models.Model):
    tags = models.ManyToManyField(
        'Tag',
        related_name='tag_recipes',
        verbose_name='Рецепт'
    )
    author = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name='user_recipes',
        verbose_name='Автор рецепта'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    name = models.CharField(max_length=200, verbose_name='Название блюда')
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField(verbose_name='Рецепт')
    cooking_time = models.DurationField(
        verbose_name='Время приготовления, мин.',
        default=RECIPE_MIN_COOKING_TIME
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(cooking_time__gte=RECIPE_MIN_COOKING_TIME),
                name=f'cooking_time__gte_{str(RECIPE_MIN_COOKING_TIME)}_minute'
            ),
            models.UniqueConstraint(
                fields=[
                    'author', 'name', 'text', 'cooking_time'
                ],
                name='unique_recipe'
            ),
        ]
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:20]


class Tag(models.Model):
    name = models.CharField(unique=True, max_length=200)
    color = models.CharField(unique=True, max_length=7)
    slug = models.SlugField(unique=True, max_length=200)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    measurement = models.ForeignKey(
        'Measurement',
        on_delete=models.PROTECT,
        related_name='ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.DecimalField(
        max_digits=9,
        decimal_places=3,
        verbose_name='Количество'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['measurement', 'amount'],
                name='unique_ingredient_amount'
            ),
            models.CheckConstraint(
                check=models.Q(amount__gt=INGREDIENT_MIN_AMOUNT),
                name=f'amount__gt_{INGREDIENT_MIN_AMOUNT}'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return str(self.measurement)


class Measurement(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Компонент'
    )
    measurement_unit = models.CharField(
        max_length=100,
        verbose_name='Единица измерения'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_measurement'
            )
        ]
        verbose_name = 'Компонент',
        verbose_name_plural = 'Компоненты'

    def __str__(self):
        return self.name[:20]
