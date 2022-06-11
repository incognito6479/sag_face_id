from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)

"""
When Creating a simple User use manage.py createsuperuser and remove is_superuser is_staff
"""
class UserManager(BaseUserManager):
    def create_user(self, username, password=None):
        if not username:
            raise ValueError('Users must have an username')
        user = self.model(username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        u = self.create_user(username=username, password=password)
        u.is_superuser = True
        u.is_active = True
        u.is_admin = True
        u.is_staff = True
        u.save(using=self._db)
        return u

"""
When Creating a simple User use manage.py createsuperuser and remove is_superuser is_staff
"""
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(verbose_name='Username', max_length=255, unique=True)
    department = models.ForeignKey('faceapp.Department', null=True, blank=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'


class Department(models.Model):
    name = models.CharField(max_length=255, verbose_name="Отдел")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"


class WorkingHours(models.Model):
    start_time = models.TimeField(verbose_name="От")
    end_time = models.TimeField(verbose_name="До")

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"

    class Meta:
        verbose_name = "Рабочее время"
        verbose_name_plural = "Рабочее время"


class Employee(models.Model):
    department = models.ForeignKey('faceapp.Department', related_name='employee_department', on_delete=models.PROTECT, verbose_name="Отдел")
    working_hours = models.ForeignKey('faceapp.WorkingHours', on_delete=models.PROTECT, verbose_name="Рабочее время")
    person_id = models.CharField(max_length=1000, unique=True, verbose_name="ID сотрудника", blank=True, null=True)
    card_number = models.CharField(max_length=1000, unique=True, verbose_name="Номер карты", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=255, verbose_name="Имя")
    last_name = models.CharField(max_length=255, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=255, verbose_name="Отчество")
    birth_day = models.IntegerField(verbose_name="Дата рождения", blank=True, null=True)
    full_name = models.CharField(max_length=500, blank=True, null=True)
    status = models.BooleanField(default=True, verbose_name="Статус сотрудника")
    image = models.ImageField(upload_to='employee_image', verbose_name="Фото сотрудника")
    comment = models.TextField(blank=True, null=True, verbose_name="Подробнее о сотруднике")

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_name = f"{self.last_name} {self.first_name} {self.middle_name}"
        super(Employee, self).save()

    class Meta:
        verbose_name = "Сотрудники"
        verbose_name_plural = "Сотрудники"


class Attendance(models.Model):
    EMPLOYEE_CHECK_STATUS = (
        ('checkOut', 'Выход'),
        ('checkIn', 'Вход')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('faceapp.Employee', on_delete=models.PROTECT, verbose_name="Сотрудник")
    check_status = models.CharField(max_length=255, choices=EMPLOYEE_CHECK_STATUS, verbose_name='Состояние входа')
    time = models.DateTimeField(verbose_name="Время", blank=True, null=True)

    def __str__(self):
        return f"{self.user} {self.check_status}"

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"


class DepartmentShiftTime(models.Model):
    department = models.ForeignKey('faceapp.Department', on_delete=models.PROTECT, verbose_name="Отдел")
    shift_time = models.BooleanField(default=True, verbose_name="Работа по сменам")

    def __str__(self):
        return f"{self.department}"

    class Meta:
        verbose_name = "Сменный рабочий"
        verbose_name_plural = "Сменный рабочий"


class CalendarWorkingDays(models.Model):
    date_from = models.DateField(verbose_name="Дата от")
    date_to = models.DateField(verbose_name="Дата до", blank=True, null=True)
    difference = models.IntegerField(verbose_name="Количество дней", default=0)

    def __str__(self):
        return f"{self.date_from} - {self.date_to}"

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.date_to:
            self.difference = 1
        else:
            self.difference = abs(self.date_to - self.date_from).days + 1
        super(CalendarWorkingDays, self).save()

    class Meta:
        verbose_name = "Календарь выходных"
        verbose_name_plural = "Календарь выходных"


class EmployeeVacation(models.Model):
    date_from = models.DateField(verbose_name="Дата от")
    date_to = models.DateField(verbose_name="Дата до", blank=True, null=True)
    employee = models.ForeignKey('faceapp.Employee', on_delete=models.PROTECT, verbose_name="Сотрудник")
    difference = models.IntegerField(verbose_name="Количество дней", default=0)

    def __str__(self):
        return f"{self.employee}"

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.date_to:
            self.difference = 1
        else:
            self.difference = abs(self.date_to - self.date_from).days + 1
        super(EmployeeVacation, self).save()

    class Meta:
        verbose_name = "Отпуск"
        verbose_name_plural = "Отпуск"


class EmployeeBusinessTrip(models.Model):
    date_from = models.DateField(verbose_name="Дата от")
    date_to = models.DateField(verbose_name="Дата до", blank=True, null=True)
    employee = models.ForeignKey('faceapp.Employee', on_delete=models.PROTECT, verbose_name="Сотрудник")
    difference = models.IntegerField(verbose_name="Количество дней", default=0)

    def __str__(self):
        return f"{self.employee}"

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.date_to:
            self.difference = 1
        else:
            self.difference = abs(self.date_to - self.date_from).days + 1
        super(EmployeeBusinessTrip, self).save()

    class Meta:
        verbose_name = "Командировки"
        verbose_name_plural = "Командировки"
        permissions = (
            ("can_add_business_trip", "Can add Business trip"),
        )


class CsvImporter(models.Model):
    last_updated_time = models.DateTimeField(verbose_name="Время последнего импорта")

    def __str__(self):
        return f"{self.last_updated_time}"

    class Meta:
        verbose_name = "Время последнего импорта"
        verbose_name_plural = "Время последнего импорта"
        permissions = (
            ("can_add_csv_importer", "Can add CSV importer"),
        )