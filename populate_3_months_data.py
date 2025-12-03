"""
Script para poblar la base de datos con 3 meses de datos históricos.
Crea:
- 1 empresa
- 1 supervisor
- 15 empleados
- Dispositivos para cada empleado
- 3 meses de datos de sensores (jornadas de 8-12 horas)
- Alertas de fatiga
- Recomendaciones
- Reportes de síntomas
- Descansos programados
"""

import os
import sys
import django
from datetime import datetime, timedelta, time
import random
import pytz
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.devices.models import Device
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation, SymptomReport, ScheduledBreak
from django.utils import timezone

User = get_user_model()


# Configuración
COMPANY_NAME = "TechCorp Industries S.A."
NUM_EMPLOYEES = 15
START_DATE = datetime.now(pytz.UTC) - timedelta(days=90)  # 3 meses atrás
END_DATE = datetime.now(pytz.UTC)

# Nombres y apellidos para generar empleados
FIRST_NAMES = [
    "Carlos", "María", "José", "Ana", "Luis", "Carmen", "Miguel", "Laura",
    "Francisco", "Isabel", "Antonio", "Patricia", "Manuel", "Rosa", "Pedro"
]
LAST_NAMES = [
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Sánchez",
    "Ramírez", "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Cruz", "Morales"
]

DEPARTMENTS = ["Producción", "Mantenimiento", "Logística", "Calidad", "Operaciones"]
POSITIONS = ["Operario", "Técnico", "Supervisor de Línea", "Operador de Máquina", "Inspector"]


def create_company():
    """Crea la empresa"""
    print(f"\n📦 Creando empresa: {COMPANY_NAME}")
    
    company, created = Company.objects.get_or_create(
        name=COMPANY_NAME,
        defaults={
            'contact_email': 'contacto@techcorp.com',
            'contact_phone': '+52 55 1234 5678',
            'address': 'Av. Industria 1234, Ciudad de México',
            'is_active': True,
            'subscription_start': (START_DATE - timedelta(days=30)).date(),
            'max_employees': 50
        }
    )
    
    if created:
        print(f"   ✅ Empresa creada: {company.name}")
    else:
        print(f"   ℹ️  Empresa ya existía: {company.name}")
    
    return company


def create_supervisor(company):
    """Crea el supervisor de la empresa"""
    print(f"\n👔 Creando supervisor para {company.name}")
    
    supervisor, created = User.objects.get_or_create(
        email='supervisor@techcorp.com',
        defaults={
            'first_name': 'Roberto',
            'last_name': 'Méndez',
            'role': 'supervisor',
            'company': company,
            'phone': '+52 55 9876 5432',
            'department': 'Dirección',
            'position': 'Supervisor General',
            'is_active': True
        }
    )
    
    if created:
        supervisor.set_password('supervisor123')
        supervisor.save()
        print(f"   ✅ Supervisor creado: {supervisor.get_full_name()} ({supervisor.email})")
        print(f"   🔑 Password: supervisor123")
    else:
        print(f"   ℹ️  Supervisor ya existía: {supervisor.get_full_name()}")
    
    return supervisor


def create_employees(company, supervisor, num_employees=15):
    """Crea los empleados"""
    print(f"\n👥 Creando {num_employees} empleados")
    
    employees = []
    
    for i in range(num_employees):
        email = f'empleado{i+1:02d}@techcorp.com'
        first_name = FIRST_NAMES[i]
        last_name = LAST_NAMES[i]
        department = random.choice(DEPARTMENTS)
        position = random.choice(POSITIONS)
        
        employee, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'role': 'employee',
                'company': company,
                'supervisor': supervisor,
                'phone': f'+52 55 {random.randint(1000, 9999)} {random.randint(1000, 9999)}',
                'department': department,
                'position': position,
                'is_active': True
            }
        )
        
        if created:
            employee.set_password('empleado123')
            employee.save()
            print(f"   ✅ Empleado {i+1:02d}: {employee.get_full_name()} - {department} ({email})")
        
        employees.append(employee)
    
    print(f"\n   📊 Total empleados creados/verificados: {len(employees)}")
    return employees


def create_devices(employees, supervisor, company):
    """Crea dispositivos para cada empleado"""
    print(f"\n📱 Creando dispositivos ESP32")
    
    devices = []
    
    for i, employee in enumerate(employees):
        device_id = f"ESP32-{i+1:03d}"
        
        device, created = Device.objects.get_or_create(
            device_identifier=device_id,
            defaults={
                'employee': employee,
                'supervisor': supervisor,
                'company': company,
                'is_active': True,
                'last_connection': timezone.now()
            }
        )
        
        if created:
            print(f"   ✅ Dispositivo {device_id} asignado a {employee.get_full_name()}")
        
        devices.append(device)
    
    print(f"\n   📊 Total dispositivos creados: {len(devices)}")
    return devices


def generate_workday_hours():
    """Genera hora de inicio y duración de jornada laboral (8-12 horas)"""
    # Turnos comunes
    shift_starts = [
        time(6, 0),   # Turno matutino
        time(7, 0),
        time(8, 0),
        time(14, 0),  # Turno vespertino
        time(22, 0),  # Turno nocturno
    ]
    
    start_time = random.choice(shift_starts)
    duration_hours = random.randint(8, 12)
    
    return start_time, duration_hours


def generate_sensor_data_for_day(device, employee, date, start_time, duration_hours):
    """Genera datos de sensores para un día completo de trabajo"""
    
    # Convertir a datetime con zona horaria
    start_datetime = datetime.combine(date, start_time)
    start_datetime = pytz.UTC.localize(start_datetime)
    end_datetime = start_datetime + timedelta(hours=duration_hours)
    
    sensor_readings = []
    processed_metrics = []
    
    # Parámetros base del empleado (varían por persona)
    base_hr = random.randint(60, 75)
    base_spo2 = random.uniform(96, 99)
    
    # Generar datos cada 5 minutos (para no sobrecargar)
    current_time = start_datetime
    reading_interval = timedelta(minutes=5)
    
    fatigue_factor = 0  # Aumenta conforme avanza el día
    
    while current_time < end_datetime:
        hours_worked = (current_time - start_datetime).total_seconds() / 3600
        
        # Fatiga aumenta progresivamente
        fatigue_factor = min(hours_worked / duration_hours, 1.0)
        
        # Simular incremento de HR y disminución de SpO2 por fatiga
        hr_variation = random.uniform(-5, 10 + fatigue_factor * 20)
        spo2_variation = random.uniform(-fatigue_factor * 3, 1)
        
        heart_rate = base_hr + hr_variation
        spo2 = max(88, min(100, base_spo2 + spo2_variation))
        
        # Movimiento aleatorio (mayor al inicio, menor con fatiga)
        activity = random.uniform(0.1, 1.0 - fatigue_factor * 0.3)
        
        sensor_data = SensorData(
            device=device,
            timestamp=current_time,
            heart_rate=heart_rate,
            spo2=spo2,
            accel_x=random.uniform(-activity, activity),
            accel_y=random.uniform(-activity, activity),
            accel_z=random.uniform(-activity, activity)
        )
        sensor_readings.append(sensor_data)
        
        # Cada 30 minutos crear métricas procesadas
        if len(sensor_readings) % 6 == 0:
            window_start = current_time - timedelta(minutes=30)
            window_end = current_time
            
            # Calcular índice de fatiga (aumenta con el tiempo)
            fatigue_index = min(fatigue_factor * 100 + random.uniform(-10, 10), 100)
            
            metric = ProcessedMetrics(
                device=device,
                employee=employee,
                window_start=window_start,
                window_end=window_end,
                hr_avg=heart_rate,
                hr_max=heart_rate + random.uniform(0, 10),
                hr_min=heart_rate - random.uniform(0, 5),
                hrv_rmssd=random.uniform(20, 80),
                hrv_sdnn=random.uniform(30, 100),
                hr_trend='stable' if fatigue_factor < 0.5 else 'increasing',
                spo2_avg=spo2,
                spo2_min=spo2 - random.uniform(0, 2),
                spo2_variance=random.uniform(0, 2),
                desaturation_count=int(fatigue_factor * 3),
                activity_level=activity,
                movement_variance=random.uniform(0.1, 0.5),
                movement_entropy=random.uniform(0.5, 2.0),
                posture_angle=random.uniform(-15, 15),
                fatigue_index=fatigue_index,
                hr_activity_ratio=heart_rate / (activity + 0.1),
                recovery_time=random.uniform(1, 10)
            )
            processed_metrics.append(metric)
        
        current_time += reading_interval
    
    return sensor_readings, processed_metrics, fatigue_factor


def create_sensor_data_bulk(devices, employees, start_date, end_date):
    """Crea datos de sensores en bulk para todos los empleados durante 3 meses"""
    print(f"\n📊 Generando datos de sensores para {len(employees)} empleados durante 3 meses...")
    print(f"   Desde: {start_date.date()}")
    print(f"   Hasta: {end_date.date()}")
    
    total_days = (end_date - start_date).days
    print(f"   Total días: {total_days}")
    
    all_sensor_data = []
    all_processed_metrics = []
    daily_fatigue_levels = {}  # Para generar alertas después
    
    current_date = start_date.date()
    day_count = 0
    
    while current_date <= end_date.date():
        day_count += 1
        
        # Cada empleado trabaja ~5 días a la semana
        for device, employee in zip(devices, employees):
            # 70% de probabilidad de trabajar cada día (simula días libres)
            if random.random() > 0.3:
                start_time, duration = generate_workday_hours()
                
                sensor_data, processed_metrics, end_fatigue = generate_sensor_data_for_day(
                    device, employee, current_date, start_time, duration
                )
                
                all_sensor_data.extend(sensor_data)
                all_processed_metrics.extend(processed_metrics)
                
                # Guardar nivel de fatiga final del día
                if employee.id not in daily_fatigue_levels:
                    daily_fatigue_levels[employee.id] = []
                daily_fatigue_levels[employee.id].append({
                    'date': current_date,
                    'fatigue': end_fatigue,
                    'duration': duration
                })
        
        # Mostrar progreso cada 10 días
        if day_count % 10 == 0:
            print(f"   📅 Procesados {day_count}/{total_days} días...")
        
        current_date += timedelta(days=1)
    
    # Guardar en bulk (mucho más rápido)
    print(f"\n   💾 Guardando {len(all_sensor_data)} lecturas de sensores...")
    SensorData.objects.bulk_create(all_sensor_data, batch_size=1000)
    
    print(f"   💾 Guardando {len(all_processed_metrics)} métricas procesadas...")
    ProcessedMetrics.objects.bulk_create(all_processed_metrics, batch_size=500)
    
    print(f"   ✅ Datos de sensores guardados exitosamente")
    
    return daily_fatigue_levels


def create_alerts_and_recommendations(employees, supervisor, daily_fatigue_levels, start_date, end_date):
    """Crea alertas y recomendaciones basadas en los niveles de fatiga"""
    print(f"\n⚠️  Generando alertas de fatiga y recomendaciones...")
    
    all_alerts = []
    all_recommendations = []
    
    for employee in employees:
        if employee.id not in daily_fatigue_levels:
            continue
        
        fatigue_history = daily_fatigue_levels[employee.id]
        
        for day_data in fatigue_history:
            fatigue = day_data['fatigue']
            date = day_data['date']
            
            # Generar alerta si la fatiga es alta (>0.6)
            if fatigue > 0.6 and random.random() < 0.4:  # 40% de probabilidad
                alert_time = datetime.combine(date, time(random.randint(10, 18), random.randint(0, 59)))
                alert_time = pytz.UTC.localize(alert_time)
                
                severity = 'high' if fatigue > 0.8 else 'medium'
                fatigue_index = fatigue * 100
                
                alert = FatigueAlert(
                    employee=employee,
                    supervisor=supervisor,
                    timestamp=alert_time,
                    severity=severity,
                    alert_type='high_fatigue',
                    message=f'Nivel alto de fatiga detectado: {fatigue_index:.1f}%',
                    fatigue_index=fatigue_index,
                    is_acknowledged=random.random() < 0.7,  # 70% reconocidas
                    is_resolved=random.random() < 0.5  # 50% resueltas
                )
                
                if alert.is_acknowledged:
                    alert.acknowledged_at = alert_time + timedelta(minutes=random.randint(5, 120))
                    alert.acknowledged_by = supervisor
                
                if alert.is_resolved:
                    alert.resolved_at = alert_time + timedelta(hours=random.randint(1, 8))
                    alert.resolved_by = supervisor
                
                all_alerts.append(alert)
        
        # Generar recomendaciones periódicas (cada 2-3 semanas)
        weeks = (end_date - start_date).days // 7
        num_recommendations = random.randint(weeks // 2, weeks)
        
        for _ in range(num_recommendations):
            rec_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            
            rec_types = ['break', 'task_redistribution', 'shift_rotation']
            rec_type = random.choice(rec_types)
            
            descriptions = {
                'break': f'Se recomienda programar descansos adicionales para {employee.get_full_name()} debido a patrones de fatiga acumulada.',
                'task_redistribution': f'Considerar redistribuir tareas de alta carga física para {employee.get_full_name()}.',
                'shift_rotation': f'Evaluar rotación de turnos para {employee.get_full_name()} para mejorar recuperación.'
            }
            
            recommendation = RoutineRecommendation(
                supervisor=supervisor,
                employee=employee,
                recommendation_type=rec_type,
                description=descriptions[rec_type],
                priority=random.randint(2, 4),
                based_on_data={
                    'avg_fatigue_last_week': random.uniform(0.4, 0.8),
                    'high_fatigue_days': random.randint(2, 5)
                },
                is_applied=random.random() < 0.4,  # 40% aplicadas
                created_at=rec_date
            )
            
            if recommendation.is_applied:
                recommendation.applied_at = rec_date + timedelta(days=random.randint(1, 7))
            
            all_recommendations.append(recommendation)
    
    # Guardar en bulk
    print(f"   💾 Guardando {len(all_alerts)} alertas...")
    FatigueAlert.objects.bulk_create(all_alerts, batch_size=500)
    
    print(f"   💾 Guardando {len(all_recommendations)} recomendaciones...")
    RoutineRecommendation.objects.bulk_create(all_recommendations, batch_size=500)
    
    print(f"   ✅ Alertas y recomendaciones creadas")


def create_symptom_reports(employees, start_date, end_date):
    """Crea reportes de síntomas de los empleados"""
    print(f"\n🏥 Generando reportes de síntomas...")
    
    all_reports = []
    
    symptom_types = ['fatigue', 'headache', 'dizziness', 'muscle_pain', 'eye_strain', 'stress']
    
    for employee in employees:
        # Cada empleado reporta síntomas ocasionalmente (5-15 veces en 3 meses)
        num_reports = random.randint(5, 15)
        
        for _ in range(num_reports):
            report_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            
            report = SymptomReport(
                employee=employee,
                symptom_type=random.choice(symptom_types),
                severity=random.choice(['mild', 'moderate', 'severe']),
                description=f'Síntoma reportado durante jornada laboral.',
                is_reviewed=random.random() < 0.6,  # 60% revisados
                created_at=report_date
            )
            
            if report.is_reviewed:
                report.reviewed_at = report_date + timedelta(hours=random.randint(1, 24))
                report.reviewed_by = employee.supervisor
                report.notes = 'Revisado y documentado.'
            
            all_reports.append(report)
    
    print(f"   💾 Guardando {len(all_reports)} reportes de síntomas...")
    SymptomReport.objects.bulk_create(all_reports, batch_size=500)
    
    print(f"   ✅ Reportes de síntomas creados")


def create_scheduled_breaks(employees, start_date, end_date):
    """Crea descansos programados"""
    print(f"\n☕ Generando descansos programados...")
    
    all_breaks = []
    
    break_types = ['coffee', 'lunch', 'rest', 'stretch']
    
    for employee in employees:
        # Cada empleado programa varios descansos a la semana
        # ~3 meses = 12 semanas, ~3 descansos por semana = 36 descansos
        num_breaks = random.randint(30, 45)
        
        for _ in range(num_breaks):
            break_date = start_date.date() + timedelta(days=random.randint(0, (end_date - start_date).days))
            break_time = time(random.randint(9, 16), random.choice([0, 15, 30, 45]))
            
            scheduled_break = ScheduledBreak(
                employee=employee,
                break_type=random.choice(break_types),
                scheduled_date=break_date,
                scheduled_time=break_time,
                duration_minutes=random.choice([15, 30, 45, 60]),
                reason='Descanso programado',
                status=random.choice(['completed', 'completed', 'completed', 'pending', 'approved']),
                created_at=datetime.combine(break_date - timedelta(days=random.randint(0, 2)), time(8, 0))
            )
            
            if scheduled_break.status in ['approved', 'completed']:
                scheduled_break.reviewed_by = employee.supervisor
                scheduled_break.reviewed_at = datetime.combine(break_date, time(8, 0))
            
            all_breaks.append(scheduled_break)
    
    print(f"   💾 Guardando {len(all_breaks)} descansos programados...")
    ScheduledBreak.objects.bulk_create(all_breaks, batch_size=500)
    
    print(f"   ✅ Descansos programados creados")


def create_admin():
    """Crea el usuario administrador del sistema"""
    print(f"\n👨‍💼 Creando usuario administrador del sistema")
    
    admin, created = User.objects.get_or_create(
        email='admin@fatiguedetection.com',
        defaults={
            'first_name': 'Admin',
            'last_name': 'Sistema',
            'role': 'admin',
            'company': None,  # Admin no pertenece a ninguna empresa
            'phone': '+52 55 0000 0000',
            'department': 'Administración',
            'position': 'Administrador del Sistema',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f"   ✅ Admin creado: {admin.get_full_name()} ({admin.email})")
        print(f"   🔑 Password: admin123")
    else:
        print(f"   ℹ️  Admin ya existía: {admin.get_full_name()}")
    
    return admin


def main():
    """Función principal"""
    print("=" * 80)
    print("🚀 INICIANDO POBLACIÓN DE BASE DE DATOS - 3 MESES DE DATOS")
    print("=" * 80)
    
    # Crear estructura base
    admin = create_admin()
    company = create_company()
    supervisor = create_supervisor(company)
    employees = create_employees(company, supervisor, NUM_EMPLOYEES)
    devices = create_devices(employees, supervisor, company)
    
    # Generar datos históricos
    daily_fatigue = create_sensor_data_bulk(devices, employees, START_DATE, END_DATE)
    
    # Generar alertas y recomendaciones
    create_alerts_and_recommendations(employees, supervisor, daily_fatigue, START_DATE, END_DATE)
    
    # Generar reportes y descansos
    create_symptom_reports(employees, START_DATE, END_DATE)
    create_scheduled_breaks(employees, START_DATE, END_DATE)
    
    # Resumen final
    print("\n" + "=" * 80)
    print("✅ POBLACIÓN DE BASE DE DATOS COMPLETADA")
    print("=" * 80)
    print(f"\n📊 RESUMEN:")
    print(f"   • Admin del sistema: {admin.get_full_name()} ({admin.email})")
    print(f"   • Empresa: {company.name}")
    print(f"   • Supervisor: {supervisor.get_full_name()} ({supervisor.email})")
    print(f"   • Empleados: {len(employees)}")
    print(f"   • Dispositivos: {len(devices)}")
    print(f"   • Lecturas de sensores: {SensorData.objects.count():,}")
    print(f"   • Métricas procesadas: {ProcessedMetrics.objects.count():,}")
    print(f"   • Alertas de fatiga: {FatigueAlert.objects.count():,}")
    print(f"   • Recomendaciones: {RoutineRecommendation.objects.count():,}")
    print(f"   • Reportes de síntomas: {SymptomReport.objects.count():,}")
    print(f"   • Descansos programados: {ScheduledBreak.objects.count():,}")
    print(f"\n🔑 CREDENCIALES DE ACCESO:")
    print(f"   Admin: admin@fatiguedetection.com / admin123")
    print(f"   Supervisor: supervisor@techcorp.com / supervisor123")
    print(f"   Empleados: empleadoXX@techcorp.com / empleado123 (XX = 01 a 15)")
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
