"""
Management command to create initial demo data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authentication.models import Employee
from apps.devices.models import Device

User = get_user_model()


class Command(BaseCommand):
    help = 'Create initial demo users and data'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')
        
        # Create admin
        if not User.objects.filter(email='admin@stressmonitor.com').exists():
            admin = User.objects.create_superuser(
                email='admin@stressmonitor.com',
                username='admin',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role=User.Role.ADMIN
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created admin: {admin.email}'))
        
        # Create supervisor
        if not User.objects.filter(email='supervisor@stressmonitor.com').exists():
            supervisor = User.objects.create_user(
                email='supervisor@stressmonitor.com',
                username='supervisor',
                password='supervisor123',
                first_name='María',
                last_name='Supervisora',
                role=User.Role.SUPERVISOR
            )
            Employee.objects.create(
                user=supervisor,
                employee_id='SUP-001',
                position='Supervisor de Operaciones',
                department='Operaciones'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created supervisor: {supervisor.email}'))
        else:
            supervisor = User.objects.get(email='supervisor@stressmonitor.com')
        
        # Create employees
        employees_data = [
            {
                'email': 'juan.perez@stressmonitor.com',
                'username': 'jperez',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'employee_id': 'EMP-001',
                'position': 'Desarrollador',
                'department': 'TI'
            },
            {
                'email': 'maria.gonzalez@stressmonitor.com',
                'username': 'mgonzalez',
                'first_name': 'María',
                'last_name': 'González',
                'employee_id': 'EMP-002',
                'position': 'Analista',
                'department': 'Operaciones'
            },
            {
                'email': 'carlos.lopez@stressmonitor.com',
                'username': 'clopez',
                'first_name': 'Carlos',
                'last_name': 'López',
                'employee_id': 'EMP-003',
                'position': 'QA Tester',
                'department': 'TI'
            }
        ]
        
        for emp_data in employees_data:
            if not User.objects.filter(email=emp_data['email']).exists():
                user = User.objects.create_user(
                    email=emp_data['email'],
                    username=emp_data['username'],
                    password='employee123',
                    first_name=emp_data['first_name'],
                    last_name=emp_data['last_name'],
                    role=User.Role.EMPLOYEE
                )
                
                Employee.objects.create(
                    user=user,
                    employee_id=emp_data['employee_id'],
                    position=emp_data['position'],
                    department=emp_data['department'],
                    supervisor=supervisor
                )
                
                # Create a device for each employee
                Device.objects.create(
                    employee=user,
                    device_type=Device.DeviceType.WATCH,
                    hardware_id=f'WATCH-{emp_data["employee_id"]}',
                    model_name='Redmi Watch 5 Active',
                    firmware_version='1.0.0'
                )
                
                self.stdout.write(self.style.SUCCESS(f'✓ Created employee: {user.email}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Demo data created successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin: admin@stressmonitor.com / admin123')
        self.stdout.write('  Supervisor: supervisor@stressmonitor.com / supervisor123')
        self.stdout.write('  Employee: juan.perez@stressmonitor.com / employee123')
