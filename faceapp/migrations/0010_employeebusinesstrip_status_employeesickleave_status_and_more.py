# Generated by Django 4.0.4 on 2022-10-05 05:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faceapp', '0009_user_employee_alter_attendance_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeebusinesstrip',
            name='status',
            field=models.CharField(blank=True, choices=[('waiting', 'В ожидание'), ('accepted', 'Принято'), ('rejected', 'Отклонено')], max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='employeesickleave',
            name='status',
            field=models.CharField(blank=True, choices=[('waiting', 'В ожидание'), ('accepted', 'Принято'), ('rejected', 'Отклонено')], max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='employeevacation',
            name='status',
            field=models.CharField(blank=True, choices=[('waiting', 'В ожидание'), ('accepted', 'Принято'), ('rejected', 'Отклонено')], max_length=255, null=True),
        ),
    ]