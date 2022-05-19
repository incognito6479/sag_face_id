from django.contrib import admin
from faceapp.models import Employee, Attendance, WorkingHours, Department


@admin.register(Employee)
class EmployeeModelAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'middle_name', 'department', 'working_hours', 'status')
    search_fields = ('first_name', 'last_name', 'department')


@admin.register(Attendance)
class EmployeeModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'check_status', 'time')


@admin.register(WorkingHours)
class EmployeeModelAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time')


@admin.register(Department)
class EmployeeModelAdmin(admin.ModelAdmin):
    pass
