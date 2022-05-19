from django.db import models


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
    department = models.ForeignKey('faceapp.Department', on_delete=models.PROTECT, verbose_name="Отдел")
    working_hours = models.ForeignKey('faceapp.WorkingHours', on_delete=models.PROTECT, verbose_name="Рабочее время")
    person_id = models.CharField(max_length=1000, unique=True, verbose_name="ID сотрудника")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=255, verbose_name="Имя")
    last_name = models.CharField(max_length=255, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=255, verbose_name="Отчество")
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
    # check_out = models.DateTimeField(verbose_name="Выход", blank=True, null=True)

    def __str__(self):
        return f"{self.user} {self.check_status}"

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"
