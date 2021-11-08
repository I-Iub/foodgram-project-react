# Generated by Django 3.2.9 on 2021-11-08 19:14

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_auto_20211108_2211'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='ingredient',
            name='amount__gt_0',
        ),
        migrations.RemoveConstraint(
            model_name='recipe',
            name='cooking_time__gte_1_minute',
        ),
        migrations.AddConstraint(
            model_name='ingredient',
            constraint=models.CheckConstraint(check=models.Q(('amount__gt', 0)), name='amount__gt_0'),
        ),
        migrations.AddConstraint(
            model_name='recipe',
            constraint=models.CheckConstraint(check=models.Q(('cooking_time__gte', datetime.timedelta(seconds=60))), name='cooking_time__gte_0:01:00_minute'),
        ),
    ]
