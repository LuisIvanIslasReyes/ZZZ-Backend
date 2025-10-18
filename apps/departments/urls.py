"""
Department URLs
"""
from django.urls import path
from .views import (
    DepartmentListCreateView,
    DepartmentDetailView,
    DepartmentEmployeesView,
    DepartmentAddEmployeeView,
    DepartmentRemoveEmployeeView,
    DepartmentAnalyticsView,
    WorkShiftListCreateView,
    WorkShiftDetailView,
    WorkShiftEmployeesView,
    WorkShiftAssignEmployeeView,
)

app_name = 'departments'

urlpatterns = [
    # Departments
    path('', DepartmentListCreateView.as_view(), name='department_list'),
    path('<int:pk>/', DepartmentDetailView.as_view(), name='department_detail'),
    path('<int:pk>/employees/', DepartmentEmployeesView.as_view(), name='department_employees'),
    path('<int:pk>/employees/add/', DepartmentAddEmployeeView.as_view(), name='department_add_employee'),
    path('<int:pk>/employees/<int:user_id>/', DepartmentRemoveEmployeeView.as_view(), name='department_remove_employee'),
    path('<int:pk>/analytics/', DepartmentAnalyticsView.as_view(), name='department_analytics'),
    
    # Work Shifts
    path('workshifts/', WorkShiftListCreateView.as_view(), name='workshift_list'),
    path('workshifts/<int:pk>/', WorkShiftDetailView.as_view(), name='workshift_detail'),
    path('workshifts/<int:pk>/employees/', WorkShiftEmployeesView.as_view(), name='workshift_employees'),
    path('workshifts/<int:pk>/employees/assign/', WorkShiftAssignEmployeeView.as_view(), name='workshift_assign_employee'),
]