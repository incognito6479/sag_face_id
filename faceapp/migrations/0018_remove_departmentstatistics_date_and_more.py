# Generated by Django 4.0.4 on 2022-11-04 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faceapp', '0017_departmentstatistics_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='departmentstatistics',
            name='date',
        ),
        migrations.AddField(
            model_name='departmentstatistics',
            name='month',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='departmentstatistics',
            name='year',
            field=models.IntegerField(null=True),
        ),
    ]
