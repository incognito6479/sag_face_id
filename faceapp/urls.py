from django.urls import path
from django.contrib import admin
from faceapp.views import LoginView, HomeView, LogoutView, DepartmentListView, DepartmentDetailView, EmployeeDetail, \
    ImporterView, ShiftTimeWorkers, CalendarListView, VacationListView, get_department_percentage_for_view, \
    BusinessTripView, StatisticsEmployeeTemplateView, StatisticsDepartmentTemplateView, vacation_add_func, \
    EmployeeSickLeaveView, EmployeeCreateView, EmployeeUpdateView, EmployeeDeleteView, VacationUpdateView, \
    VacationDeleteView, SickLeaveUpdateView, SickLeaveDeleteView, BusinessTripUpdateView, BusinessTripDeleteView

urlpatterns = [
    path('admin/', admin.site.urls, name="django_admin_url"),
    path('login', LoginView.as_view(), name='login_view'),
    path('logout', LogoutView.as_view(), name='logout_view'),
    path('', HomeView.as_view(), name='home_view'),
    path('importer/', ImporterView.as_view(), name='importer_view'),
    path('vacation_view/', VacationListView.as_view(), name='vacation_view'),
    path('sick_leave_view/', EmployeeSickLeaveView.as_view(), name='sick_leave_view'),
    path('sick_leave_update_view/<int:pk>/', SickLeaveUpdateView.as_view(), name='sick_leave_update_view'),
    path('sick_leave_delete_view/<int:pk>/<int:dep_id>/', SickLeaveDeleteView.as_view(), name='sick_leave_delete_view'),
    path('vacation_add_view/', vacation_add_func, name='vacation_add_view'),
    path('vacation_update_view/<int:pk>/', VacationUpdateView.as_view(), name='vacation_update_view'),
    path('vacation_delete_view/<int:pk>/<int:dep_id>/', VacationDeleteView.as_view(), name='vacation_delete_view'),
    path('shift_time_view/', ShiftTimeWorkers.as_view(), name='shift_time_view'),
    path('calendar_view/', CalendarListView.as_view(), name='calendar_view'),
    path('department/list', DepartmentListView.as_view(), name='department_list_view'),
    path('department/detail/<int:pk>/', DepartmentDetailView.as_view(), name='department_detail_view'),
    path('employe/detail/<int:pk>/', EmployeeDetail.as_view(), name='employee_detail_view'),
    path('employe/delete/<int:pk>/<int:dep_id>/', EmployeeDeleteView.as_view(), name='employee_delete_view'),
    path('employe/create/<int:pk>/<str:name>/', EmployeeCreateView.as_view(), name='employee_create_view'),
    path('employe/update/<int:pk>/<int:department_id>/<str:name>/', EmployeeUpdateView.as_view(),
         name='employee_update_view'),
    path('business_trip_view/', BusinessTripView.as_view(), name='business_trip_view'),
    path('business_trip_update_view/<int:pk>/', BusinessTripUpdateView.as_view(), name='business_trip_update_view'),
    path('business_trip_delete_view/<int:pk>/<int:dep_id>/', BusinessTripDeleteView.as_view(),
         name='business_trip_delete_view'),
    path('statistics_employee_view/', StatisticsEmployeeTemplateView.as_view(), name='statistics_employee_view'),
    path('statistics_department_view/', StatisticsDepartmentTemplateView.as_view(), name='statistics_department_view'),
    path('department_percentage_ajax/', get_department_percentage_for_view, name='department_percentage_ajax'),
]
