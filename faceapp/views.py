from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime, timedelta

from faceapp.models import Attendance, Employee, Department
from system.settings import SERVER_TIME_DIFFERENCE


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


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login_view')


class DepartmentListView(ListView):
    model = Department
    template_name = 'templates/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        queryset = Department.objects.all()
        if self.request.GET.get('name'):
            queryset = queryset.filter(name__icontains=self.request.GET.get('name'))
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DepartmentListView, self).get_context_data(**kwargs)
        if self.request.GET.get('name'):
            context['name'] = self.request.GET.get('name')
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
        queryset = {}
        for user in users:
            for attendance in attendances:
                if attendance.user.person_id == user.person_id:
                    if user.person_id not in queryset:
                        queryset[user.person_id] = [{
                            'full_name': f"{user.last_name} {user.first_name} {user.middle_name}",
                            'check_status': attendance.get_check_status_display(),
                            'time': attendance.time,
                            'department': user.department,
                            'img': user.image,
                            'start_time_difference':
                                attendance.time.hour + SERVER_TIME_DIFFERENCE - user.working_hours.start_time.hour,
                            'end_time_difference':
                                user.working_hours.end_time.hour - (attendance.time.hour + SERVER_TIME_DIFFERENCE)
                        }]
                    else:
                        queryset[user.person_id].append({
                            'full_name': f"{user.last_name} {user.first_name} {user.middle_name}",
                            'check_status': attendance.get_check_status_display(),
                            'time': attendance.time,
                            'department': user.department,
                            'img': user.image,
                            'start_time_difference':
                                attendance.time.hour + SERVER_TIME_DIFFERENCE - user.working_hours.start_time.hour,
                            'end_time_difference':
                                user.working_hours.end_time.hour - (attendance.time.hour + SERVER_TIME_DIFFERENCE)
                        })
                else:
                    if user.person_id not in queryset:
                        queryset[user.person_id] = [{
                            'full_name': f"{user.last_name} {user.first_name} {user.middle_name}",
                            'check_status': "---",
                            'time': "---",
                            'department': user.department,
                            'img': user.image,
                            'start_time_difference': 1,
                            'end_time_difference': 1,
                        }]
        return queryset
