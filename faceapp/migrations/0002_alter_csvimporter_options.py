# Generated by Django 4.0.4 on 2022-06-08 05:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('faceapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='csvimporter',
            options={'permissions': (('can_add_csv_importer', 'Can add CSV importer'),), 'verbose_name': 'Время последнего импорта', 'verbose_name_plural': 'Время последнего импорта'},
        ),
    ]
