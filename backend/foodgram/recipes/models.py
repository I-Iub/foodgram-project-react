from django.db import models
from users.models import User


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
    image = models.ImageField()
    text = models.TextField(verbose_name='Рецепт')
    cooking_time = models.DateTimeField(  # сделать валидацию (>= 1)
        verbose_name='Время приготовления, мин.'
    )

    class Meta:
        def __str__(self):
            return self.name[:20]


class Tag(models.Model):
    name = models.CharField(unique=True, max_length=200)
    color = models.ImageField(unique=True, max_length=7)
    slug = models.SlugField(unique=True, max_length=200)

    class Meta:
        def __str__(self):
            return self.name


class Ingredient(models.Model):
    measurement_unit = models.ForeignKey(
        'Measurement',
        on_delete=models.PROTECT,
        related_name='ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.DecimalField(  # сделать валидацию > 0
        max_digits=9,
        decimal_places=3,
        verbose_name='Количество'
    )

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['measurement_unit', 'amount'],
            name='unique_ingredient_amount'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

        def __str__(self):
            return self.measurement_unit


class Measurement(models.Model):
    name = models.CharField(
        max_length=200,
        verboes_name='Компонент'
    )
    measure = models.CharField(
        max_length=100,
        verbose_name='Единица измерения'
    )

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['name', 'measure'],
            name='unique_measurement'
            )
        ]
        verbose_name = 'Компонент',
        verbose_name_plural = 'Компоненты'
