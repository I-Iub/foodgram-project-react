# Generated by Django 3.2.9 on 2021-11-19 19:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0009_alter_recipe_tags'),
        ('organizer', '0005_alter_subscription_author'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shoppingcart',
            name='recipe',
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='recipe',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='shopping_cart_of_recipe', to='recipes.recipe', verbose_name='Рецепт'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_shopping_cart', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
    ]
