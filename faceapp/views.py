import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import View, ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count
from datetime import datetime, timedelta

from faceapp.forms import EmployeeModelForm, VacationModelForm, SickLeaveModelForm, BusinessTripModelForm
from faceapp.helpers import get_employee_detail_attendances, get_all_employees_attendances, \
    get_attendance_percentage_employee, get_attendance_percentage_department, \
    get_statistics_employee_working_hours_ajax, dry_list_of_years
from faceapp.models import Attendance, Employee, Department, DepartmentShiftTime, CalendarWorkingDays, \
    EmployeeVacation, CsvImporter, EmployeeBusinessTrip, DepartmentStatistics, EmployeeStatisticsAttendance, \
    EmployeeStatisticsWorkingHours, EmployeeSickLeave, User, MONTH_LIST
from faceapp.tasks import importer_attendance
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from system.settings import PROGRAM_STARTED_YEAR


class BusinessTripDeleteView(LoginRequiredMixin, DeleteView):
    model = EmployeeBusinessTrip
    success_url = reverse_lazy('business_trip_view')
    login_url = "login_url"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff and self.request.user.department_id == self.kwargs['dep_id']:
                return super(BusinessTripDeleteView, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class BusinessTripUpdateView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            obj = EmployeeBusinessTrip.objects.select_related('employee__department').get(id=self.kwargs['pk'])
            if self.request.user.is_staff and self.request.user.department_id == obj.employee.department_id or \
                    self.request.user.is_superuser:
                return super(BusinessTripUpdateView, self).dispatch(request, *args, **kwargs)
        return PermissionDenied()

    def get(self, request, pk):
        obj = EmployeeBusinessTrip.objects.select_related('employee__department').get(id=pk)
        form = BusinessTripModelForm(instance=obj)
        form.fields['employee'].queryset = Employee.objects.filter(department_id=obj.employee.department_id)
        context = {
            'form': form,
            'dep_id': obj.employee.department_id,
            'pk': pk
        }
        return render(request, 'templates/business_trip/business_trip_update.html', context)

    def post(self, request, pk):
        form = BusinessTripModelForm(request.POST, instance=EmployeeBusinessTrip.objects.get(id=pk))
        if form.is_valid():
            form.save()
            return redirect("business_trip_view")
        context = {
            'form': form.errors
        }
        return render(request, 'templates/business_trip/business_trip_update.html', context)


class SickLeaveDeleteView(LoginRequiredMixin, DeleteView):
    model = EmployeeSickLeave
    success_url = reverse_lazy('sick_leave_view')
    login_url = "login_url"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff and self.request.user.department_id == self.kwargs['dep_id']:
                return super(SickLeaveDeleteView, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class SickLeaveUpdateView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            obj = EmployeeSickLeave.objects.select_related('employee__department').get(id=self.kwargs['pk'])
            if self.request.user.is_staff and self.request.user.department_id == obj.employee.department_id or \
                    self.request.user.is_superuser:
                return super(SickLeaveUpdateView, self).dispatch(request, *args, **kwargs)
        return PermissionDenied()

    def get(self, request, pk):
        obj = EmployeeSickLeave.objects.select_related('employee__department').get(id=pk)
        form = SickLeaveModelForm(instance=obj)
        form.fields['employee'].queryset = Employee.objects.filter(department_id=obj.employee.department_id)
        context = {
            'form': form,
            'dep_id': obj.employee.department_id,
            'pk': pk
        }
        return render(request, 'templates/sick_leave/sick_leave_update.html', context)

    def post(self, request, pk):
        form = SickLeaveModelForm(request.POST, instance=EmployeeSickLeave.objects.get(id=pk))
        if form.is_valid():
            form.save()
            return redirect("sick_leave_view")
        context = {
            'form': form.errors
        }
        return render(request, 'templates/sick_leave/sick_leave_update.html', context)


class VacationDeleteView(LoginRequiredMixin, DeleteView):
    model = EmployeeVacation
    success_url = reverse_lazy('vacation_view')
    login_url = "login_url"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff and self.request.user.department_id == self.kwargs['dep_id']:
                return super(VacationDeleteView, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()


class VacationUpdateView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            obj = EmployeeVacation.objects.select_related('employee__department').get(id=self.kwargs['pk'])
            if self.request.user.is_staff and self.request.user.department_id == obj.employee.department_id or \
                    self.request.user.is_superuser:
                return super(VacationUpdateView, self).dispatch(request, *args, **kwargs)
        return PermissionDenied()

    def get(self, request, pk):
        obj = EmployeeVacation.objects.select_related('employee__department').get(id=pk)
        form = VacationModelForm(instance=obj)
        form.fields['employee'].queryset = Employee.objects.filter(department_id=obj.employee.department_id)
        context = {
            'form': form,
            'dep_id': obj.employee.department_id,
            'pk': pk
        }
        return render(request, 'templates/vacation/vacation_update.html', context)

    def post(self, request, pk):
        form = VacationModelForm(request.POST, instance=EmployeeVacation.objects.get(id=pk))
        if form.is_valid():
            form.save()
            return redirect("vacation_view")
        context = {
            'form': form
        }
        return render(request, 'templates/vacation/vacation_update.html', context)


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    login_url = "login_view"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff and self.request.user.department_id == self.kwargs['dep_id']:
                return super(EmployeeDeleteView, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()

    def get_success_url(self):
        User.objects.filter(employee_id=self.object.id).delete()
        return reverse("department_detail_view", kwargs={'pk': self.kwargs['dep_id']})


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeModelForm
    template_name = 'employee/employee_create.html'
    login_url = 'login_view'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff and self.request.user.department_id == self.kwargs['department_id']:
                return super(EmployeeUpdateView, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()

    def get_context_data(self, **kwargs):
        context = super(EmployeeUpdateView, self).get_context_data(**kwargs)
        context['department_id'] = self.kwargs['department_id']
        context['department_name'] = self.kwargs['name']
        context['employee_id'] = self.kwargs['pk']
        context['update'] = 1
        user = User.objects.filter(employee_id=self.kwargs['pk']).first()
        context['username_value'] = user.username if user else ""
        return context

    def form_invalid(self, form):
        return HttpResponse(form.errors)

    def form_valid(self, form):
        check_username = User.objects.filter(username=self.request.POST.get('username'))
        if not check_username or self.request.POST.get('username') == check_username[0].username:
            user, created = User.objects.get_or_create(employee_id=self.kwargs['pk'], defaults={
                "username": self.request.POST.get('username'),
                "password": make_password(self.request.POST.get('password')),
                "department_id": self.kwargs['department_id']
            })
            if not created:
                user.username = self.request.POST.get('username')
                user.password = make_password(self.request.POST.get('password'))
                user.department_id = self.kwargs['department_id']
                user.save()
            return super(EmployeeUpdateView, self).form_valid(form)
        context = self.get_context_data()
        context['username_error'] = 1
        return render(self.request, self.template_name, context)

    def get_success_url(self):
        return reverse("department_detail_view", kwargs={'pk': self.kwargs['department_id']})


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeModelForm
    template_name = 'employee/employee_create.html'
    login_url = 'login_view'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff and self.request.user.department_id == self.kwargs['pk']:
                return super(EmployeeCreateView, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied()

    def get_context_data(self, **kwargs):
        context = super(EmployeeCreateView, self).get_context_data(**kwargs)
        context['department_id'] = self.kwargs['pk']
        context['department_name'] = self.kwargs['name']
        return context

    def form_invalid(self, form):
        return HttpResponse(form.errors)

    def form_valid(self, form):
        f = form.save(commit=False)
        f.department_id = self.kwargs['pk']
        check_username = User.objects.filter(username=self.request.POST.get('username'))
        if not check_username:
            f.save()
            User.objects.create(username=self.request.POST.get('username'),
                                password=make_password(self.request.POST.get('password')),
                                employee_id=f.id,
                                department_id=self.kwargs['pk'])
            return super(EmployeeCreateView, self).form_valid(f)
        context = self.get_context_data()
        context['username_error'] = 1
        return render(self.request, self.template_name, context)

    def get_success_url(self):
        return reverse("department_detail_view", kwargs={'pk': self.kwargs['pk']})


class EmployeeSickLeaveView(LoginRequiredMixin, View):
    def get(self, request):
        employee_obj = Employee.objects.filter(department_id=self.request.user.department_id)
        sick_leave_obj = EmployeeSickLeave.objects.select_related('employee').all()
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            sick_leave_obj = sick_leave_obj.filter(employee_id=self.request.user.employee_id)
        if self.request.user.is_staff:
            sick_leave_obj = sick_leave_obj.filter(employee__department_id=self.request.user.department_id)
        context = {
            'employee_obj': employee_obj,
            'sick_leave_obj': sick_leave_obj,
            'sick_leave_obj_user': sick_leave_obj.values('employee_id', 'employee__full_name'),
        }
        return render(request, 'templates/sick_leave.html', context)

    def post(self, request):
        status = 'waiting'
        employee_id = None
        if self.request.user.is_staff:
            status = 'accepted'
            employee_id = self.request.POST.get('employee_add_selected')
        else:
            employee_id = self.request.user.employee_id
        EmployeeSickLeave.objects.create(
            date_from=datetime.fromisoformat(self.request.POST.get('date_from')),
            date_to=datetime.fromisoformat(self.request.POST.get('date_to')),
            employee_id=employee_id,
            comment=self.request.POST.get('comment')
        )
        return redirect('sick_leave_view')


class StatisticsEmployeeTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'templates/statistics_employee.html'
    login_url = 'login_view'

    def get_context_data(self, **kwargs):
        context = super(StatisticsEmployeeTemplateView, self).get_context_data(**kwargs)
        year = self.request.GET.get('year', None)
        month = self.request.GET.get('month', None)
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        emp_att = EmployeeStatisticsAttendance.objects.filter(year=year, month=month)
        empl_wh = EmployeeStatisticsWorkingHours.objects.filter(year=year, month=month)
        context['attendances_h'] = emp_att.filter(type="highest").order_by('-percentage')
        context['attendances_l'] = emp_att.filter(type="lowest").order_by('percentage')
        context['working_hours_h'] = empl_wh.filter(type="highest").order_by('-hours')
        context['working_hours_l'] = empl_wh.filter(type="lowest").order_by('percentage')
        context['list_of_years'] = dry_list_of_years()
        context['list_of_months'] = MONTH_LIST
        context['month'] = month
        context['year'] = year
        return context


class StatisticsDepartmentTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'templates/statistics_department.html'
    login_url = 'login_view'

    def get_context_data(self, **kwargs):
        context = super(StatisticsDepartmentTemplateView, self).get_context_data(**kwargs)
        year = self.request.GET.get('year', None)
        month = self.request.GET.get('month', None)
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        # dep_percentage = DepartmentStatistics.objects.all()
        dep_percentage = DepartmentStatistics.objects.filter(year=year, month=month)
        context['department_statistics_h'] = dep_percentage.filter(type="highest").order_by('-percentage')
        context['department_statistics_l'] = dep_percentage.filter(type="lowest").order_by('percentage')
        context['list_of_years'] = dry_list_of_years()
        context['list_of_months'] = MONTH_LIST
        context['month'] = month
        context['year'] = year
        # print(datetime.today())
        return context


class BusinessTripView(LoginRequiredMixin, View):
    def get(self, request):
        employee_obj = Employee.objects.filter(department_id=self.request.user.department_id)
        business_trips = EmployeeBusinessTrip.objects.select_related('employee__department').all().order_by('-id')
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            business_trips = business_trips.filter(employee_id=self.request.user.employee_id)
        if self.request.user.is_staff:
            business_trips = business_trips.filter(employee__department_id=self.request.user.department_id)
        if self.request.GET.get('employee_id'):
            business_trips = business_trips.filter(employee_id=self.request.GET.get('employee_id'))
        context = {
            'employees': employee_obj,
            'business_trips': business_trips,
            'department_id': self.request.user.department_id
        }
        return render(request, 'templates/trip.html', context)

    def post(self, request):
        status = 'waiting'
        employee_id = None
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        comment = request.POST.get('comment')
        if self.request.user.is_staff:
            status = 'accepted'
            employee_id = request.POST['employee_ids_from_select2'].split(',')
            for i in employee_id:
                EmployeeBusinessTrip.objects.create(
                    date_from=datetime.fromisoformat(date_from),
                    date_to=datetime.fromisoformat(date_to),
                    employee_id=i,
                    comment=comment,
                    status=status)
        else:
            employee_id = self.request.user.employee_id
            EmployeeBusinessTrip.objects.create(
                date_from=datetime.fromisoformat(date_from),
                date_to=datetime.fromisoformat(date_to),
                employee_id=employee_id,
                comment=comment,
                status=status)
        return redirect('business_trip_view')


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
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            queryset = queryset.filter(employee_id=self.request.user.employee_id)
        if self.request.user.is_staff:
            queryset = queryset.filter(employee__department_id=self.request.user.department_id)
        if self.request.GET.get('employee_id'):
            queryset = queryset.filter(employee_id=self.request.GET.get('employee_id'))
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(VacationListView, self).get_context_data(**kwargs)
        employee_queryset = EmployeeVacation.objects.select_related('employee').all()
        employee_obj = Employee.objects.filter(department_id=self.request.user.department_id)
        if not self.request.user.is_superuser:
            employee_queryset = employee_queryset.filter(employee__department_id=self.request.user.department_id)
        context['employees'] = employee_queryset.values("employee__full_name", "employee_id").distinct()
        context['employee_obj'] = employee_obj
        return context


def vacation_add_func(request):
    if request.method == 'POST' and request.user.is_authenticated:
        employee_id = None
        status = 'waiting'
        if request.user.is_staff:
            employee_id = request.POST.get('employee_add_selected')
            status = 'accepted'
        else:
            employee_id = request.user.employee_id
        EmployeeVacation.objects.create(
            date_from=datetime.fromisoformat(request.POST.get('date_from')),
            date_to=datetime.fromisoformat(request.POST.get('date_to')),
            employee_id=employee_id,
            status=status
        )
        return redirect('vacation_view')
    raise PermissionDenied()


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
        queryset = Department.objects.prefetch_related('employee_department').all() \
            .annotate(employee_number=Count('employee_department'))
        if self.request.GET.get('name'):
            queryset = queryset.filter(name__icontains=self.request.GET.get('name'))
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DepartmentListView, self).get_context_data(**kwargs)
        context['name'] = self.request.GET.get('name') if self.request.GET.get('name') else ""
        return context


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    login_url = 'login_view'
    template_name = 'templates/department_detail.html'
    model = Department
    context_object_name = 'department'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            self.object = self.get_object()
            if self.request.user.department_id == self.object.id or self.request.user.is_superuser:
                return super(DepartmentDetailView, self).dispatch(request, *args, **kwargs)
            raise PermissionDenied()
        return redirect('login_view')

    def get_context_data(self, **kwargs):
        context = super(DepartmentDetailView, self).get_context_data(**kwargs)
        employees = Employee.objects.filter(department_id=self.kwargs['pk'], status=True)
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

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            self.object = self.get_object()
            if self.request.user.employee_id == self.object.id or self.request.user.is_superuser or \
                    self.request.user.is_staff and self.request.user.department_id == self.object.department_id:
                return super(EmployeeDetail, self).dispatch(request, *args, **kwargs)
            raise PermissionDenied()
        return redirect('login_view')

    def get_context_data(self, **kwargs):
        context = super(EmployeeDetail, self).get_context_data(**kwargs)
        attendances = Attendance.objects.filter(user_id=self.kwargs['pk']).order_by('time')
        if self.request.GET.get('date_to') and self.request.GET.get('date_from'):
            context['date_to'] = datetime.fromisoformat(self.request.GET.get('date_to'))
            context['date_from'] = datetime.fromisoformat(self.request.GET.get('date_from'))
            attendances = attendances.filter(
                time__range=(self.request.GET.get('date_from'), self.request.GET.get('date_to')))
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
            context['date_to'] = datetime.fromisoformat(self.request.GET.get('date_to'))
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
                                             time__day=time_var.split(' ')[0].split('-')[2], )
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            attendances = attendances.filter(user_id=self.request.user.employee_id)
            users = users.filter(id=self.request.user.employee_id)
        if self.request.user.is_staff:
            attendances = attendances.filter(user__department_id=self.request.user.department_id)
            users = users.filter(department_id=self.request.user.department_id)
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
            'last_time_visit': last_updated_time,
            'list_of_months': MONTH_LIST,
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
        print('IMPORTER STARTED')
        month_to_import = self.request.POST.get('month')
        importer_attendance.delay(int(month_to_import))
        # importer_attendance(int(month_to_import))
        print('IMPORTER ENDED')
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
