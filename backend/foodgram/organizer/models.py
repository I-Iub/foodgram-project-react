from django.db import models
from recipes.models import Recipe
from users.models import User


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.PROTECT,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return (f'Список покупок. Запись {self.id}; '
                f'Пользователь {self.user.username}')


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_on_author',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('user')),
                name='user_is_not_author'
            )
        ]
        ordering = ['user']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return (f'Подписка id={self.id} пользователя {self.user.first_name}'
                f'{self.user.last_name}')


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.PROTECT,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return (f'Избранное {self.user.username}: рецепт id={self.recipe.id}')
