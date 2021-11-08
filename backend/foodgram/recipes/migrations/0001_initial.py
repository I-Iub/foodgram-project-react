# Generated by Django 3.2.9 on 2021-11-08 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=3, max_digits=9, verbose_name='Количество')),
            ],
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиенты',
            },
        ),
        migrations.CreateModel(
            name='Measurement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Компонент')),
                ('measure', models.CharField(max_length=100, verbose_name='Единица измерения')),
            ],
            options={
                'verbose_name': ('Компонент',),
                'verbose_name_plural': 'Компоненты',
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название блюда')),
                ('image', models.ImageField(upload_to='')),
                ('text', models.TextField(verbose_name='Рецепт')),
                ('cooking_time', models.DateTimeField(verbose_name='Время приготовления, мин.')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('color', models.ImageField(max_length=7, unique=True, upload_to='')),
                ('slug', models.SlugField(max_length=200, unique=True)),
            ],
        ),
    ]
