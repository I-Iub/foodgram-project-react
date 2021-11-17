# Generated by Django 3.2.9 on 2021-11-17 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_remove_recipe_unique_recipe'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='recipe',
            constraint=models.UniqueConstraint(fields=('author', 'name', 'text', 'cooking_time'), name='unique_recipe'),
        ),
    ]
