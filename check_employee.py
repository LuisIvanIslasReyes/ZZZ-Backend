import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser

emp = CustomUser.objects.get(id=6)
print(f"Empleado: {emp.email}")
print(f"Nombre: {emp.get_full_name()}")
print(f"Supervisor: {emp.supervisor}")
print(f"Supervisor ID: {emp.supervisor.id if emp.supervisor else 'None'}")
print(f"Company: {emp.company}")
print(f"Company ID: {emp.company.id if emp.company else 'None'}")
