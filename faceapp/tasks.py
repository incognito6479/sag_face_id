from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.shortcuts import render

from faceapp.helpers import save_importer_csv_to_attendance, get_attendance_percentage_department


@shared_task
def importer_attendance():
    save_importer_csv_to_attendance()
    return


# @shared_task
# def department_percentage(request, employee_obj):
#     context = {
#         'department_percentage': get_attendance_percentage_department(employee_obj)
#     }
#     return render(request, 'templates/department_detail.html', context)