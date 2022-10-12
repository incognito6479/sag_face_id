# Generated by Django 4.0.4 on 2022-06-18 10:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('faceapp', '0002_alter_csvimporter_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmentshifttime',
            name='department',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shift_time_department', to='faceapp.department', verbose_name='Отдел'),
        ),
    ]
