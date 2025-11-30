import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.devices.models import Device

devices = Device.objects.all()
print(f'\n{"="*60}')
print(f'DISPOSITIVOS EN LA BASE DE DATOS')
print(f'{"="*60}')
print(f'Total: {devices.count()}')
print(f'{"="*60}\n')

for d in devices:
    print(f'ID: {d.id}')
    print(f'Device ID: {d.device_identifier}')
    print(f'Empleado: {d.employee.get_full_name()} ({d.employee.email})')
    print(f'Supervisor: {d.supervisor.get_full_name() if d.supervisor else "None"}')
    print(f'Company: {d.company.name if d.company else "None"}')
    print(f'Activo: {d.is_active}')
    print(f'Creado: {d.created_at}')
    print(f'{"-"*60}\n')
