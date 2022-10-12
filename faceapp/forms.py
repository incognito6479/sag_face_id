from django.forms import ModelForm, CharField, DateField, DateInput
from faceapp.models import Employee, EmployeeVacation, EmployeeSickLeave, EmployeeBusinessTrip


class EmployeeModelForm(ModelForm):
    username = CharField(max_length=255, label='Login', required=True)
    password = CharField(max_length=500, label="Пароль", required=True)

    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'middle_name', 'birth_day', 'image',
                  'card_number', 'person_id', 'working_hours', 'created_at', 'username', 'password']
        widgets = {
            'created_at': DateInput(attrs={'class': 'datepicker-here'})
        }


class VacationModelForm(ModelForm):
    date_to = DateField(
        label="Дата до",
        widget=DateInput(attrs={'class': 'datepicker-here'})
    )
    date_from = DateField(
        label="Дата от",
        widget=DateInput(attrs={'class': 'datepicker-here'})
    )

    class Meta:
        model = EmployeeVacation
        fields = ['date_from', 'date_to', 'employee', 'status']


class SickLeaveModelForm(ModelForm):
    date_to = DateField(
        label="Дата до",
        widget=DateInput(attrs={'class': 'datepicker-here'})
    )
    date_from = DateField(
        label="Дата от",
        widget=DateInput(attrs={'class': 'datepicker-here'})
    )

    class Meta:
        model = EmployeeSickLeave
        fields = ['date_from', 'date_to', 'employee', 'status']


class BusinessTripModelForm(ModelForm):
    date_to = DateField(
        label="Дата до",
        widget=DateInput(attrs={'class': 'datepicker-here'})
    )
    date_from = DateField(
        label="Дата от",
        widget=DateInput(attrs={'class': 'datepicker-here'})
    )

    class Meta:
        model = EmployeeBusinessTrip
        fields = ['date_from', 'date_to', 'employee', 'status']

