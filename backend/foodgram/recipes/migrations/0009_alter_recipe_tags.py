# Generated by Django 3.2.9 on 2021-11-19 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_alter_recipe_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(related_name='tag_recipes', to='recipes.Tag', verbose_name='Тэг'),
        ),
    ]
