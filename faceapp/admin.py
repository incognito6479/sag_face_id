from django.contrib import admin
from faceapp.models import Employee, Attendance, WorkingHours, Department, DepartmentShiftTime, EmployeeVacation, \
    CalendarWorkingDays, CsvImporter, EmployeeBusinessTrip, User, EmployeeSickLeave
from django.contrib.auth.models import Group


admin.site.unregister(Group)
admin.site.register(User)


@admin.register(EmployeeSickLeave)
class EmployeeSickLeaveModelAdmin(admin.ModelAdmin):
    list_display = "employee", "date_from", "date_to", "difference", "status"
    exclude = ('difference',)


@admin.register(Employee)
class EmployeeModelAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'middle_name', 'department', 'working_hours', 'status', 'created_at')
    search_fields = ('full_name', 'person_id', 'card_number')
    exclude = ('full_name',)
    # list_editable = ['created_at']


# @admin.register(Attendance)
# class EmployeeModelAdmin(admin.ModelAdmin):
#     search_fields = ('user__full_name',)
#     list_display = ('user', 'check_status', 'time')


@admin.register(WorkingHours)
class WorkingHoursModelAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time')


@admin.register(Department)
class DepartmentModelAdmin(admin.ModelAdmin):
    pass


@admin.register(EmployeeBusinessTrip)
class EmployeeBusinessTripModelAdmin(admin.ModelAdmin):
    list_display = "employee", "date_from", "date_to", "difference", "status"
    exclude = ('difference',)


# @admin.register(CsvImporter)
# class CsvImporterModelAdmin(admin.ModelAdmin):
#     pass


@admin.register(DepartmentShiftTime)
class DepartmentShiftTimeModelAdmin(admin.ModelAdmin):
    list_display = "department", "shift_time"


@admin.register(EmployeeVacation)
class EmployeeVacationModelAdmin(admin.ModelAdmin):
    list_display = "employee", "date_from", "date_to", "difference", "status"
    exclude = ('difference',)


@admin.register(CalendarWorkingDays)
class CalendarModelAdmin(admin.ModelAdmin):
    list_display = "date_from", "date_to", 'difference'
    exclude = ('difference',)
