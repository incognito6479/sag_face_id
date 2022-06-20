import json

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View, ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count
from datetime import datetime, timedelta

from faceapp.helpers import get_employee_detail_attendances, get_all_employees_attendances, \
    get_attendance_percentage_employee, get_attendance_percentage_department, get_statistics_employee_attendance
from faceapp.models import Attendance, Employee, Department, DepartmentShiftTime, CalendarWorkingDays, \
    EmployeeVacation, CsvImporter, EmployeeBusinessTrip
from faceapp.tasks import importer_attendance
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings


class StatisticsEmployeeTemplateView(TemplateView):
    template_name = 'templates/statistics_employee.html'

    def get_context_data(self, **kwargs):
        context = super(StatisticsEmployeeTemplateView, self).get_context_data(**kwargs)
        # my_dict = {1: 20, 3: 50, 8: 80, 7: 54, 2: 96}
        # print(sorted(my_dict.keys()))
        return context


class StatisticsDepartmentTemplateView(TemplateView):
    template_name = 'templates/statistics_department.html'

    def get_context_data(self, **kwargs):
        context = super(StatisticsDepartmentTemplateView, self).get_context_data(**kwargs)
        return context


class BusinessTripView(LoginRequiredMixin, View):
    def get(self, request, pk):
        employee_obj = Employee.objects.prefetch_related('department').filter(department_id=pk)
        business_trips = EmployeeBusinessTrip.objects.select_related('employee__department')\
            .filter(employee__department_id=pk).order_by('-id')
        print(business_trips)
        context = {
            'employees': employee_obj,
            'business_trips': business_trips,
            'department_id': pk
        }
        return render(request, 'templates/trip.html', context)

    def post(self, request, pk):
        if request.user.has_perm('faceapp.can_add_business_trip') and request.user.department_id == pk:
            employees = request.POST['employee_ids_from_select2'].split(',')
            date_from = request.POST.get('date_from')
            date_to = request.POST.get('date_to')
            for i in employees:
                EmployeeBusinessTrip.objects.create(
                    date_from=datetime.fromisoformat(date_from),
                    date_to=datetime.fromisoformat(date_to),
                    employee_id=i)
            return redirect('business_trip_view', pk=pk)
        raise PermissionDenied()


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home_view')
        return render(request, 'templates/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('home_view')
        context = {
            'login_error': 'Логин или пароль неверен'
        }
        return render(request, 'templates/login.html', context)


class LogoutView(LoginRequiredMixin, View):
    login_url = 'login_view'

    def get(self, request):
        logout(request)
        return redirect('login_view')


class ShiftTimeWorkers(LoginRequiredMixin, ListView):
    model = DepartmentShiftTime
    template_name = 'templates/shift_time_workers.html'
    context_object_name = 'shift_time_workers'
    login_url = 'login_view'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ShiftTimeWorkers, self).get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        return context


class VacationListView(LoginRequiredMixin, ListView):
    model = EmployeeVacation
    template_name = 'templates/vacation.html'
    context_object_name = 'vacations'
    login_url = 'login_view'

    def get_queryset(self):
        queryset = EmployeeVacation.objects.select_related('employee').all()
        if self.request.GET.get('employee_id'):
            queryset = queryset.filter(employee_id=self.request.GET.get('employee_id'))
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(VacationListView, self).get_context_data(**kwargs)
        context['employees'] = EmployeeVacation.objects.select_related('employee').all()\
                                .values("employee__full_name", "employee_id").distinct()
        return context


class CalendarListView(LoginRequiredMixin, ListView):
    model = CalendarWorkingDays
    template_name = "templates/holidays.html"
    context_object_name = 'holidays'
    login_url = 'login_view'

    def get_queryset(self):
        queryset = CalendarWorkingDays.objects.filter(date_from__year=datetime.now().year)
        if self.request.GET.get('month'):
            queryset = queryset.filter(date_from__month=self.request.GET.get('month'))
        return queryset


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'templates/department_list.html'
    context_object_name = 'departments'
    login_url = 'login_view'

    def get_queryset(self):
        queryset = Department.objects.prefetch_related('employee_department').all()\
            .annotate(employee_number=Count('employee_department'))
        if self.request.GET.get('name'):
            queryset = queryset.filter(name__icontains=self.request.GET.get('name'))
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DepartmentListView, self).get_context_data(**kwargs)
        if self.request.GET.get('name'):
            context['name'] = self.request.GET.get('name')
        return context


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    login_url = 'login_view'
    template_name = 'templates/department_detail.html'
    model = Department
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        context = super(DepartmentDetailView, self).get_context_data(**kwargs)
        employees =  Employee.objects.filter(department_id=self.kwargs['pk'], status=True)
        if not DepartmentShiftTime.objects.filter(department_id=self.kwargs['pk']):
            context['percentage'] = '1'
            context['department_id'] = self.kwargs['pk']
        if self.request.GET.get('name'):
            employees = employees.filter(full_name__icontains=self.request.GET.get('name'))
            context['name'] = self.request.GET.get('name')
        context['employees'] = employees
        context['employees_count'] = employees.count()
        return context


class EmployeeDetail(LoginRequiredMixin, DetailView):
    login_url = 'login_view'
    model = Employee
    template_name = 'templates/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super(EmployeeDetail, self).get_context_data(**kwargs)
        attendances = Attendance.objects.filter(user_id=self.kwargs['pk'])
        if self.request.GET.get('date_to') and self.request.GET.get('date_from'):
            print(self.request.GET.get('date_from'), self.request.GET.get('date_to'))
            context['date_to'] =  datetime.fromisoformat(self.request.GET.get('date_to'))
            context['date_from'] =  datetime.fromisoformat(self.request.GET.get('date_from'))
            print(context['date_from'], context['date_to'])
            attendances = attendances.filter(time__range=(self.request.GET.get('date_from'), self.request.GET.get('date_to')))
        else:
            context['date_to_show'] = datetime.today() - timedelta(days=7)
            time_var = str(datetime.today() - timedelta(days=7))
            attendances = attendances.filter(time__year=time_var.split(' ')[0].split('-')[0],
                                             time__month=time_var.split(' ')[0].split('-')[1],
                                             time__day=time_var.split(' ')[0].split('-')[2], )
        context['attendances'] = get_employee_detail_attendances(attendances, self.object)
        if not DepartmentShiftTime.objects.filter(department_id=self.object.department_id):
            context['percent'] = get_attendance_percentage_employee(self.kwargs['pk'])['percent']
        return context


class HomeView(LoginRequiredMixin, ListView):
    login_url = 'login_view'
    template_name = 'templates/home.html'
    model = Employee
    context_object_name = 'attendances'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        context['employee_count'] = Employee.objects.filter(status=True).count()
        if self.request.GET.get('name'):
            context['name'] = self.request.GET.get('name')
        if self.request.GET.get('date_to'):
            context['date_to'] = datetime.strptime(self.request.GET.get('date_to'), "%Y-%M-%d")
        else:
            context['date_to_show'] = datetime.today() - timedelta(days=7)
        if self.request.GET.get('department_id'):
            context['department_id'] = self.request.GET.get('department_id')
        return context

    def get_queryset(self):
        users = Employee.objects.filter(status=True).select_related('working_hours', 'department')
        attendances = Attendance.objects.all()
        if self.request.GET.get('name'):
            users = users.filter(full_name__icontains=self.request.GET.get('name'))
        if self.request.GET.get('department_id'):
            users = users.filter(department_id=self.request.GET.get('department_id'))
        if self.request.GET.get('date_to'):
            attendances = attendances.filter(time__year=self.request.GET.get('date_to').split('-')[0],
                                             time__month=self.request.GET.get('date_to').split('-')[1],
                                             time__day=self.request.GET.get('date_to').split('-')[2],
                                             )
        else:
            time_var = str(datetime.today() - timedelta(days=7))
            attendances = attendances.filter(time__year=time_var.split(' ')[0].split('-')[0],
                                             time__month=time_var.split(' ')[0].split('-')[1],
                                             time__day=time_var.split(' ')[0].split('-')[2],)
        queryset = get_all_employees_attendances(attendances, users)
        return queryset


class ImporterView(LoginRequiredMixin, PermissionRequiredMixin, View):
    login_url = 'login_view'
    permission_required = 'faceapp.can_add_csv_importer'

    def get(self, request):
        last_updated_time = CsvImporter.objects.all().order_by('id')
        if last_updated_time:
            last_updated_time = last_updated_time.last().last_updated_time
        context = {
            'last_time_visit': last_updated_time
        }
        return render(request, 'templates/importer.html', context)

    def post(self, request):
        file = request.FILES['importer_csv']
        if not file.name.endswith('.csv'):
            context = {
                'file_error': 'Убедитесь, что файл является файлом csv'
            }
            return render(request, 'templates/importer.html', context)
        if os.path.exists('media/attendance/importer.csv'):
            os.remove("media/attendance/importer.csv")
        os.path.join(settings.MEDIA_ROOT, default_storage.save('attendance/importer.csv', ContentFile(file.read())))
        importer_attendance(request)
        last_updated_time = CsvImporter.objects.all().order_by('id')
        if last_updated_time:
            last_updated_time = last_updated_time.last().last_updated_time
        context = {
            'importer': 'ok',
            'last_time_visit': last_updated_time
        }
        return render(request, 'templates/importer.html', context)


def get_department_percentage_for_view(request):
    data_json = json.loads(request.body)
    resp = get_attendance_percentage_department(data_json['department_id'])
    return HttpResponse(json.dumps(resp))


def get_statistics_department(request):
    department_obj = Department.objects.all()
    shift_time_workers = DepartmentShiftTime.objects.all().values('department_id')
    shift_time_workers_ids = []
    department_id_and_percent = {}
    current_month = datetime.now().month - 1
    for i in shift_time_workers:
        shift_time_workers_ids.append(i['department_id'])
    for i in department_obj:
        if i.id not in shift_time_workers_ids:
            res = get_attendance_percentage_department(i.id)
            if len(res) == 0:
                department_id_and_percent[i.id] = 0
            else:
                department_id_and_percent[i.id] = res[current_month]
    department_id_and_percent = {k: v for k, v in sorted(department_id_and_percent.items(), key=lambda item: item[1])}
    if len(department_id_and_percent) % 2 == 0:
        department_id_and_percent[len(department_id_and_percent) // 2] = 0
    lowest = {}
    highest = {}
    middle_key = len(department_id_and_percent) // 2
    key_counter = 0
    for key, value in department_id_and_percent.items():
        if key_counter >= middle_key:
            highest[key] = value
        else:
            lowest[key] = value
        key_counter += 1
    lowest_dict = []
    highest_dict = []
    for key, value in highest.items():
        for i in department_obj:
            if int(key) == int(i.id):
                highest_dict.append({'percentage': value, 'name': i.name})
    for key, value in lowest.items():
        for i in department_obj:
            if int(key) == int(i.id):
                lowest_dict.append({'percentage': value, 'name': i.name})
    context = {
        'lowest': [lowest_dict[0], lowest_dict[1], lowest_dict[2]],
        'highest': [highest_dict[-1], highest_dict[-2], highest_dict[-3]]
    }
    return HttpResponse(json.dumps(context))


def get_statistics_employee_working_hours_ajax(request):
    employee_obj = Employee.objects.filter(status=True)
    current_month = datetime.now().month - 1
    employee_percent_dict = {}
    for i in employee_obj:
        resp = get_attendance_percentage_employee(i.id)
        employee_percent_dict[resp['employee_id']] = resp['percent'][current_month]
    employee_percent_dict = {k: v for k, v in sorted(employee_percent_dict.items(), key=lambda item: item[1])}
    if len(employee_percent_dict) % 2 == 0:
        employee_percent_dict[len(employee_percent_dict) // 2] = 0
    lowest = {}
    highest = {}
    middle_key = len(employee_percent_dict) // 2
    key_counter = 0
    for key, value in employee_percent_dict.items():
        if key_counter >= middle_key:
            highest[key] = value
        else:
            lowest[key] = value
        key_counter += 1
    lowest_dict = []
    highest_dict = []
    for key, value in lowest.items():
        for i in Employee.objects.select_related('department').filter(status=True):
            if int(key) == int(i.id):
                lowest_dict.append({'percentage': value, 'full_name': i.full_name, 'department': i.department.name})
    for key, value in highest.items():
        for i in Employee.objects.select_related('department').filter(status=True):
            if int(key) == int(i.id):
                highest_dict.append({'percentage': value, 'full_name': i.full_name, 'department': i.department.name})
    highest_dict.reverse()
    context = {
        'lowest_working_hours': lowest_dict[0:10],
        'highest_working_hours': highest_dict[0:10]
    }
    return HttpResponse(json.dumps(context))


def get_statistics_employee_attendance_ajax(request):
    res = get_statistics_employee_attendance()
    res = {k: v for k, v in sorted(res.items(), key=lambda item: item[1])}
    if len(res) % 2 == 0:
        res[len(res) // 2] = 0
    lowest = {}
    highest = {}
    middle_key = len(res) // 2
    key_counter = 0
    for key, value in res.items():
        if key_counter >= middle_key:
            highest[key] = value
        else:
            lowest[key] = value
        key_counter += 1
    lowest_dict = []
    highest_dict = []
    for key, value in lowest.items():
        for i in Employee.objects.select_related('department').filter(status=True):
            if int(key) == int(i.id):
                lowest_dict.append({'percentage': value, 'full_name': i.full_name, 'department': i.department.name})
    for key, value in highest.items():
        for i in Employee.objects.select_related('department').filter(status=True):
            if int(key) == int(i.id):
                highest_dict.append({'percentage': value, 'full_name': i.full_name, 'department': i.department.name})
    highest_dict.reverse()
    context = {
        'lowest_attendance': lowest_dict[0:10],
        'highest_attendance': highest_dict[0:10]
    }
    return HttpResponse(json.dumps(context))
