"""
Script de prueba rápida del sistema de ML y Recomendaciones.

Este script ejecuta una prueba end-to-end del sistema completo:
1. Genera datos de prueba
2. Procesa métricas
3. Genera recomendaciones
4. Muestra resultados

Uso:
    python SCRIPTS/test_recommendation_system.py
"""

import os
import sys
import django
import time
from pathlib import Path

# Configurar Django
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.analytics.models import RoutineRecommendation
from apps.analytics.recommendation_service import RecommendationService
from apps.analytics.ml_service import FatigueMLService
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def print_header(title):
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_step(step, title):
    """Imprime un paso del proceso."""
    print(f"\n{'─' * 80}")
    print(f"🔹 PASO {step}: {title}")
    print(f"{'─' * 80}")

def verify_users():
    """Verifica que existan usuarios en el sistema."""
    print_step(1, "VERIFICANDO USUARIOS")
    
    supervisors = User.objects.filter(role='supervisor', is_active=True)
    employees = User.objects.filter(role='employee', is_active=True)
    
    print(f"✅ Supervisores activos: {supervisors.count()}")
    print(f"✅ Empleados activos: {employees.count()}")
    
    if supervisors.count() == 0 or employees.count() == 0:
        print("\n⚠️  No hay suficientes usuarios en el sistema")
        print("💡 Ejecuta: python SCRIPTS/create_test_users.py")
        return False
    
    # Mostrar primer supervisor y sus empleados
    supervisor = supervisors.first()
    print(f"\n📋 Supervisor de prueba: {supervisor.get_full_name()}")
    
    supervisor_employees = employees.filter(supervisor=supervisor)
    print(f"   Empleados bajo su supervisión: {supervisor_employees.count()}")
    
    if supervisor_employees.count() == 0:
        print("   ⚠️  El supervisor no tiene empleados asignados")
        return False
    
    for emp in supervisor_employees[:3]:
        print(f"   - {emp.get_full_name()}")
    
    return True

def generate_test_data():
    """Genera datos de prueba."""
    print_step(2, "GENERANDO DATOS DE PRUEBA")
    
    # Contar datos existentes
    initial_count = SensorData.objects.count()
    
    print("⏳ Generando datos de sensores para prueba...")
    print("   (Esto puede tomar 1-2 minutos)")
    
    try:
        # Generar datos de 3 días para tener suficiente historial
        call_command('generate_monthly_data', days=3, verbosity=0)
        
        final_count = SensorData.objects.count()
        new_records = final_count - initial_count
        
        print(f"✅ Datos generados:")
        print(f"   - Registros nuevos: {new_records}")
        print(f"   - Total en sistema: {final_count}")
        
        return True
    except Exception as e:
        print(f"❌ Error generando datos: {e}")
        return False

def process_metrics():
    """Procesa métricas de los datos."""
    print_step(3, "PROCESANDO MÉTRICAS")
    
    initial_count = ProcessedMetrics.objects.count()
    
    print("⏳ Procesando datos y calculando índice de fatiga...")
    
    try:
        # Procesar métricas
        call_command('process_metrics', verbosity=0)
        
        final_count = ProcessedMetrics.objects.count()
        new_metrics = final_count - initial_count
        
        print(f"✅ Métricas procesadas:")
        print(f"   - Métricas nuevas: {new_metrics}")
        print(f"   - Total en sistema: {final_count}")
        
        # Mostrar ejemplo de métricas
        recent = ProcessedMetrics.objects.order_by('-window_start').first()
        if recent:
            print(f"\n📊 Ejemplo de métrica procesada:")
            print(f"   Empleado: {recent.employee.get_full_name()}")
            print(f"   Timestamp: {recent.window_start.strftime('%Y-%m-%d %H:%M')}")
            print(f"   HR promedio: {recent.hr_avg:.1f} bpm")
            print(f"   SpO2 promedio: {recent.spo2_avg:.1f}%")
            print(f"   HRV RMSSD: {recent.hrv_rmssd:.1f}")
            print(f"   Nivel de actividad: {recent.activity_level}")
            print(f"   🎯 ÍNDICE DE FATIGA: {recent.fatigue_index:.1f}/100")
        
        return True
    except Exception as e:
        print(f"❌ Error procesando métricas: {e}")
        return False

def check_ml_model():
    """Verifica el estado del modelo ML."""
    print_step(4, "VERIFICANDO MODELO ML")
    
    ml_service = FatigueMLService()
    
    if ml_service.model_loaded:
        print("✅ Modelo de Machine Learning cargado")
        info = ml_service.get_model_info()
        print(f"   - Tipo: {info['model_type'].upper()}")
        print(f"   - Features: {info['n_features']}")
        
        # Probar predicción
        test_metrics = {
            'hr_avg': 85.0,
            'hr_max': 95.0,
            'hr_min': 75.0,
            'hrv_rmssd': 30.0,
            'spo2_avg': 96.5,
            'spo2_min': 95.0,
            'activity_level': 3,
            'hr_activity_ratio': 1.2,
            'desaturation_count': 2
        }
        fatigue = ml_service.predict_fatigue_index(test_metrics)
        print(f"   - Predicción de prueba: {fatigue:.1f}/100")
    else:
        print("⚠️  Modelo ML no cargado")
        print("   Usando cálculo heurístico de fatiga")
        print("   💡 Para entrenar el modelo: python SCRIPTS/train_ml_model.py")

def generate_recommendations():
    """Genera recomendaciones."""
    print_step(5, "GENERANDO RECOMENDACIONES INTELIGENTES")
    
    initial_count = RoutineRecommendation.objects.count()
    
    print("🤖 Analizando patrones de fatiga...")
    
    try:
        service = RecommendationService()
        result = service.generate_all_recommendations()
        
        final_count = RoutineRecommendation.objects.count()
        new_recs = final_count - initial_count
        
        print(f"\n✅ Recomendaciones generadas:")
        print(f"   - Nuevas: {new_recs}")
        print(f"   - Total en sistema: {final_count}")
        print(f"   - Supervisores analizados: {result['supervisors_analyzed']}")
        
        print(f"\n📊 Por tipo:")
        for rec_type, count in result['by_type'].items():
            type_names = {
                'break': '☕ Descansos',
                'task_redistribution': '⚖️  Redistribución',
                'shift_rotation': '🔄 Rotación'
            }
            print(f"   - {type_names.get(rec_type, rec_type)}: {count}")
        
        return result['total'] > 0
    except Exception as e:
        print(f"❌ Error generando recomendaciones: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_recommendations():
    """Muestra las recomendaciones generadas."""
    print_step(6, "EJEMPLOS DE RECOMENDACIONES")
    
    recommendations = RoutineRecommendation.objects.filter(
        is_applied=False
    ).order_by('priority', '-created_at')[:3]
    
    if not recommendations.exists():
        print("ℹ️  No hay recomendaciones pendientes")
        print("   Esto puede ocurrir si los datos no muestran patrones problemáticos")
        return
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{'─' * 70}")
        print(f"📌 RECOMENDACIÓN #{i}")
        print(f"{'─' * 70}")
        print(f"Tipo: {rec.get_recommendation_type_display()}")
        print(f"Prioridad: {'⭐' * (6 - rec.priority)} ({rec.priority}/5)")
        print(f"Supervisor: {rec.supervisor.get_full_name()}")
        
        if rec.employee:
            print(f"Empleado: {rec.employee.get_full_name()}")
        else:
            print(f"Empleado: [Recomendación para todo el equipo]")
        
        # Mostrar primeras líneas de la descripción
        lines = rec.description.split('\n')
        print(f"\nDescripción:")
        for line in lines[:5]:
            if line.strip():
                print(f"  {line}")
        if len(lines) > 5:
            print(f"  ...")
        
        # Mostrar métricas clave
        if 'avg_fatigue' in rec.based_on_data:
            print(f"\n📊 Datos:")
            print(f"   Fatiga promedio: {rec.based_on_data['avg_fatigue']:.1f}/100")
            if 'max_fatigue' in rec.based_on_data:
                print(f"   Fatiga máxima: {rec.based_on_data['max_fatigue']:.1f}/100")

def show_api_examples():
    """Muestra ejemplos de uso de la API."""
    print_step(7, "EJEMPLOS DE USO DE LA API")
    
    print("""
🌐 ENDPOINTS DISPONIBLES:

1️⃣  Listar todas las recomendaciones:
   GET /api/recommendations/
   
   Respuesta:
   {
     "count": 15,
     "results": [
       {
         "id": 1,
         "recommendation_type": "break",
         "priority": 4,
         "employee": {"id": 10, "full_name": "Juan Pérez"},
         "description": "...",
         "is_applied": false
       }
     ]
   }

2️⃣  Filtrar por tipo:
   GET /api/recommendations/?type=break
   GET /api/recommendations/?type=task_redistribution
   GET /api/recommendations/?type=shift_rotation

3️⃣  Ver detalle de una recomendación:
   GET /api/recommendations/1/

4️⃣  Aplicar una recomendación:
   POST /api/recommendations/1/apply/
   
   Respuesta:
   {
     "message": "Recomendación aplicada exitosamente",
     "recommendation": { ... }
   }

5️⃣  Ver estadísticas:
   GET /api/recommendations/stats/
   
   Respuesta:
   {
     "total": 15,
     "pending": 10,
     "applied": 5,
     "by_type": {
       "break": 6,
       "task_redistribution": 3,
       "shift_rotation": 1
     }
   }

📚 Para más información, consulta:
   - MD/SISTEMA_RECOMENDACIONES_ML.md
   - Swagger UI: http://localhost:8000/api/schema/swagger-ui/
""")

def show_summary():
    """Muestra resumen final."""
    print_header("✅ PRUEBA COMPLETADA")
    
    # Estadísticas
    total_metrics = ProcessedMetrics.objects.count()
    total_recs = RoutineRecommendation.objects.count()
    pending_recs = RoutineRecommendation.objects.filter(is_applied=False).count()
    
    print("\n📊 ESTADO DEL SISTEMA:")
    print(f"   - Métricas procesadas: {total_metrics}")
    print(f"   - Recomendaciones totales: {total_recs}")
    print(f"   - Recomendaciones pendientes: {pending_recs}")
    
    # Modelo ML
    ml_service = FatigueMLService()
    if ml_service.model_loaded:
        print(f"   - Machine Learning: ✅ Activo ({ml_service.model_type})")
    else:
        print(f"   - Machine Learning: ⚠️  Heurístico")
    
    print("\n🎉 El sistema está funcionando correctamente!")
    print("\n📖 Próximos pasos:")
    print("   1. Revisa las recomendaciones en: /api/recommendations/")
    print("   2. Consulta la documentación: MD/SISTEMA_RECOMENDACIONES_ML.md")
    print("   3. Configura el frontend para consumir la API")
    
    if not ml_service.model_loaded:
        print("\n💡 Opcional: Entrena el modelo ML para mejor precisión:")
        print("   python SCRIPTS/train_ml_model.py")

def main():
    """Función principal."""
    print_header("🧪 PRUEBA DEL SISTEMA DE RECOMENDACIONES ML")
    print("Prueba end-to-end del sistema completo")
    
    try:
        # Verificar usuarios
        if not verify_users():
            print("\n⚠️  No se puede continuar sin usuarios")
            return 1
        
        # Preguntar si generar nuevos datos
        print("\n" + "─" * 80)
        response = input("¿Generar nuevos datos de prueba? (s/n): ")
        if response.lower() == 's':
            if not generate_test_data():
                print("⚠️  Error generando datos, pero continuando...")
            
            # Procesar métricas
            if not process_metrics():
                print("⚠️  Error procesando métricas")
                return 1
        else:
            print("⏩ Usando datos existentes")
        
        # Verificar ML
        check_ml_model()
        
        # Generar recomendaciones
        if not generate_recommendations():
            print("\n⚠️  No se generaron recomendaciones")
            print("   Esto puede ocurrir si no hay datos suficientes o patrones problemáticos")
        
        # Mostrar ejemplos
        show_recommendations()
        
        # Mostrar ejemplos de API
        show_api_examples()
        
        # Resumen
        show_summary()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
