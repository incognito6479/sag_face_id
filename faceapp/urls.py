from django.urls import path
from faceapp.views import LoginView, HomeView, LogoutView, DepartmentListView, DepartmentDetailView, EmployeeDetail, \
    ImporterView, ShiftTimeWorkers, CalendarListView, VacationListView, get_department_percentage_for_view, BusinessTripView, \
    StatisticsEmployeeTemplateView, StatisticsDepartmentTemplateView

urlpatterns = [
    path('login', LoginView.as_view(), name='login_view'),
    path('logout', LogoutView.as_view(), name='logout_view'),
    path('', HomeView.as_view(), name='home_view'),
    path('importer/', ImporterView.as_view(), name='importer_view'),
    path('vacation_view/', VacationListView.as_view(), name='vacation_view'),
    path('shift_time_view/', ShiftTimeWorkers.as_view(), name='shift_time_view'),
    path('calendar_view/', CalendarListView.as_view(), name='calendar_view'),
    path('department/list', DepartmentListView.as_view(), name='department_list_view'),
    path('department/detail/<int:pk>/', DepartmentDetailView.as_view(), name='department_detail_view'),
    path('employe/detail/<int:pk>/', EmployeeDetail.as_view(), name='employee_detail_view'),
    path('business_trip_view/<int:pk>/', BusinessTripView.as_view(), name='business_trip_view'),
    path('statistics_employee_view/', StatisticsEmployeeTemplateView.as_view(), name='statistics_employee_view'),
    path('statistics_department_view/', StatisticsDepartmentTemplateView.as_view(), name='statistics_department_view'),
    path('department_percentage_ajax/', get_department_percentage_for_view, name='department_percentage_ajax'),
]
