# Generated by Django 4.0.4 on 2022-10-05 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faceapp', '0013_employeestatisticsworkinghours_hours'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='created_at',
            field=models.DateTimeField(),
        ),
    ]
