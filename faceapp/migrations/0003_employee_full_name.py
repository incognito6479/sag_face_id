# Generated by Django 4.0.4 on 2022-05-17 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faceapp', '0002_remove_attendance_check_in_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='full_name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
