# Generated by Django 3.2.9 on 2021-11-20 22:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organizer', '0006_auto_20211119_2211'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subscription',
            options={'ordering': ['user'], 'verbose_name': 'Подписка', 'verbose_name_plural': 'Подписки'},
        ),
    ]