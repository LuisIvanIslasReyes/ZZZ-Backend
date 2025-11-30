from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # ==================== Autenticación ====================
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('me/', views.CurrentUserView.as_view(), name='current_user'),
    
    # ==================== Admin - Gestión de Supervisores/Empresas ====================
    # NOTA: Los supervisores son las cuentas de las empresas (1 supervisor = 1 empresa)
    path('admin/supervisors/', views.SupervisorListCreateView.as_view(), name='supervisor_list_create'),
    path('admin/supervisors/<int:pk>/', views.SupervisorDetailView.as_view(), name='supervisor_detail'),
    path('admin/stats/', views.AdminStatsView.as_view(), name='admin_stats'),
    
    # ==================== Supervisor - Gestión de Empleados ====================
    path('supervisor/employees/', views.EmployeeListCreateView.as_view(), name='employee_list_create'),
    path('supervisor/employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    
    # ==================== Empleado ====================
    path('employee/me/', views.EmployeeProfileView.as_view(), name='employee_profile'),
    path('employee/export-my-data/', views.EmployeeExportDataView.as_view(), name='employee_export_data'),
    
    # ==================== Avatar/Foto de Perfil ====================
    path('upload-avatar/', views.UploadAvatarView.as_view(), name='upload_avatar'),
]
