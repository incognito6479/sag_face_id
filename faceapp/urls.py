from django.urls import path
from faceapp.views import LoginView, HomeView, LogoutView, DepartmentListView

urlpatterns = [
    path('login', LoginView.as_view(), name='login_view'),
    path('logout', LogoutView.as_view(), name='logout_view'),
    path('', HomeView.as_view(), name='home_view'),
    path('department/list', DepartmentListView.as_view(), name='department_list_view'),
]
