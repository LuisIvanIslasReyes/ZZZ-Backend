"""
Script para configurar e integrar el sistema completo de Machine Learning y Recomendaciones.

Este script:
1. Verifica datos en la base de datos
2. Entrena el modelo ML si no existe
3. Genera recomendaciones basadas en ML
4. Muestra un reporte completo del sistema

Uso:
    python SCRIPTS/setup_ml_recommendations.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation
from apps.analytics.ml_service import FatigueMLService
from apps.analytics.recommendation_service import RecommendationService
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

def print_header(title):
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title):
    """Imprime una sección formateada."""
    print(f"\n{'─' * 80}")
    print(f"📊 {title}")
    print(f"{'─' * 80}")

def check_database_data():
    """Verifica que existan datos en la base de datos."""
    print_section("1. VERIFICANDO DATOS EN LA BASE DE DATOS")
    
    # Contar usuarios
    admins = User.objects.filter(role='admin').count()
    supervisors = User.objects.filter(role='supervisor').count()
    employees = User.objects.filter(role='employee').count()
    
    print(f"👥 Usuarios:")
    print(f"   - Administradores: {admins}")
    print(f"   - Supervisores: {supervisors}")
    print(f"   - Empleados: {employees}")
    
    if employees == 0:
        print("   ⚠️  No hay empleados en el sistema")
        return False
    
    # Contar datos de sensores
    sensor_data_count = SensorData.objects.count()
    processed_metrics_count = ProcessedMetrics.objects.count()
    
    print(f"\n📡 Datos de Sensores:")
    print(f"   - Datos crudos: {sensor_data_count}")
    print(f"   - Métricas procesadas: {processed_metrics_count}")
    
    if processed_metrics_count == 0:
        print("   ⚠️  No hay métricas procesadas")
        print("   💡 Ejecuta: python manage.py process_metrics")
        return False
    
    # Datos recientes
    recent_cutoff = timezone.now() - timedelta(days=7)
    recent_metrics = ProcessedMetrics.objects.filter(window_start__gte=recent_cutoff).count()
    
    print(f"   - Métricas últimos 7 días: {recent_metrics}")
    
    if recent_metrics < 20:
        print("   ⚠️  Datos insuficientes para análisis confiable")
        print("   💡 Genera más datos con: python SCRIPTS/esp32_simulator.py")
        return False
    
    # Contar alertas y recomendaciones actuales
    alerts_count = FatigueAlert.objects.count()
    recommendations_count = RoutineRecommendation.objects.count()
    
    print(f"\n🔔 Estado Actual del Sistema:")
    print(f"   - Alertas de fatiga: {alerts_count}")
    print(f"   - Recomendaciones generadas: {recommendations_count}")
    
    print("\n✅ Base de datos con datos suficientes para análisis")
    return True

def check_ml_model():
    """Verifica el estado del modelo de ML."""
    print_section("2. VERIFICANDO MODELO DE MACHINE LEARNING")
    
    ml_service = FatigueMLService()
    
    if ml_service.model_loaded:
        print("✅ Modelo ML cargado exitosamente")
        info = ml_service.get_model_info()
        print(f"   - Tipo de modelo: {info['model_type']}")
        print(f"   - Features utilizados: {info['n_features']}")
        
        if 'selected_features' in info and info['selected_features']:
            features_preview = ', '.join(info['selected_features'][:5])
            print(f"   - Features: {features_preview}...")
        
        if info['model_type'] == 'kmeans':
            print(f"   - Clusters: {info.get('n_clusters', 'N/A')}")
        
        return True
    else:
        print("⚠️  Modelo ML no encontrado o no se pudo cargar")
        print("   📝 El sistema usará cálculo heurístico de fatiga")
        print("\n💡 Para entrenar el modelo ML:")
        print("   1. Asegúrate de tener suficientes datos")
        print("   2. Ejecuta: python notebooks/01_data_exploration.py")
        print("   3. Ejecuta: python notebooks/02_feature_engineering.py")
        print("   4. Ejecuta: python notebooks/03_clustering_model.py")
        print("\n   O ejecuta todo con: python SCRIPTS/train_ml_model.py")
        return False

def generate_recommendations():
    """Genera recomendaciones automáticas."""
    print_section("3. GENERANDO RECOMENDACIONES INTELIGENTES")
    
    print("🤖 Analizando patrones de fatiga y generando recomendaciones...")
    
    service = RecommendationService()
    result = service.generate_all_recommendations()
    
    print(f"\n✅ Generación completada:")
    print(f"   - Total de recomendaciones: {result['total']}")
    print(f"   - Supervisores analizados: {result['supervisors_analyzed']}")
    
    print(f"\n📊 Recomendaciones por tipo:")
    for rec_type, count in result['by_type'].items():
        type_names = {
            'break': '☕ Descansos',
            'task_redistribution': '⚖️  Redistribución de tareas',
            'shift_rotation': '🔄 Rotación de turnos'
        }
        print(f"   - {type_names.get(rec_type, rec_type)}: {count}")
    
    return result

def show_recommendation_examples():
    """Muestra ejemplos de recomendaciones generadas."""
    print_section("4. EJEMPLOS DE RECOMENDACIONES GENERADAS")
    
    # Mostrar las 5 recomendaciones más prioritarias
    recommendations = RoutineRecommendation.objects.filter(
        is_applied=False
    ).order_by('priority', '-created_at')[:5]
    
    if not recommendations.exists():
        print("   ℹ️  No hay recomendaciones pendientes en este momento")
        return
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{'─' * 60}")
        print(f"📌 RECOMENDACIÓN #{i}")
        print(f"{'─' * 60}")
        print(f"Tipo: {rec.get_recommendation_type_display()}")
        print(f"Prioridad: {'⭐' * (6 - rec.priority)} ({rec.priority}/5)")
        print(f"Supervisor: {rec.supervisor.get_full_name()}")
        
        if rec.employee:
            print(f"Empleado: {rec.employee.get_full_name()}")
        else:
            print(f"Empleado: Recomendación general para el equipo")
        
        print(f"Fecha: {rec.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"\nDescripción:")
        # Mostrar solo las primeras 3 líneas de la descripción
        desc_lines = rec.description.split('\n')[:3]
        for line in desc_lines:
            print(f"  {line}")
        print(f"  ...")
        
        # Mostrar datos clave
        if 'avg_fatigue' in rec.based_on_data:
            print(f"\n📊 Métricas:")
            print(f"   - Fatiga promedio: {rec.based_on_data['avg_fatigue']:.1f}/100")
            if 'max_fatigue' in rec.based_on_data:
                print(f"   - Fatiga máxima: {rec.based_on_data['max_fatigue']:.1f}/100")

def show_system_summary():
    """Muestra un resumen completo del sistema."""
    print_section("5. RESUMEN DEL SISTEMA")
    
    # Estadísticas generales
    total_recommendations = RoutineRecommendation.objects.count()
    pending_recommendations = RoutineRecommendation.objects.filter(is_applied=False).count()
    applied_recommendations = RoutineRecommendation.objects.filter(is_applied=True).count()
    
    print(f"📊 Estado de Recomendaciones:")
    print(f"   - Total generadas: {total_recommendations}")
    print(f"   - Pendientes: {pending_recommendations}")
    print(f"   - Aplicadas: {applied_recommendations}")
    
    if total_recommendations > 0:
        applied_rate = (applied_recommendations / total_recommendations) * 100
        print(f"   - Tasa de aplicación: {applied_rate:.1f}%")
    
    # Alertas de fatiga
    total_alerts = FatigueAlert.objects.count()
    active_alerts = FatigueAlert.objects.filter(is_resolved=False).count()
    
    print(f"\n🚨 Alertas de Fatiga:")
    print(f"   - Total generadas: {total_alerts}")
    print(f"   - Activas: {active_alerts}")
    print(f"   - Resueltas: {total_alerts - active_alerts}")
    
    # Métricas de procesamiento
    recent_cutoff = timezone.now() - timedelta(hours=24)
    recent_metrics = ProcessedMetrics.objects.filter(
        window_start__gte=recent_cutoff
    ).count()
    
    print(f"\n⚙️  Procesamiento:")
    print(f"   - Métricas últimas 24h: {recent_metrics}")
    
    # Modelo ML
    ml_service = FatigueMLService()
    if ml_service.model_loaded:
        print(f"\n🤖 Machine Learning:")
        print(f"   - Estado: ✅ Modelo activo")
        print(f"   - Tipo: {ml_service.model_type.upper()}")
    else:
        print(f"\n🤖 Machine Learning:")
        print(f"   - Estado: ⚠️  Usando cálculo heurístico")

def show_usage_instructions():
    """Muestra instrucciones de uso del sistema."""
    print_section("6. CÓMO USAR EL SISTEMA")
    
    print("""
📖 FLUJO COMPLETO DEL SISTEMA:

1️⃣  RECOLECCIÓN DE DATOS:
   - Los dispositivos ESP32 envían datos cada 5 segundos vía MQTT
   - Los datos se guardan automáticamente en SensorData
   
   💡 Para simular: python SCRIPTS/esp32_simulator.py

2️⃣  PROCESAMIENTO AUTOMÁTICO:
   - Cada 2 minutos, el sistema procesa datos crudos
   - Calcula métricas avanzadas (HRV, SpO2, actividad)
   - Usa ML para calcular índice de fatiga
   - Guarda en ProcessedMetrics
   
   💡 Manual: python manage.py process_metrics

3️⃣  GENERACIÓN DE RECOMENDACIONES:
   - Analiza patrones de fatiga de últimos 7 días
   - Genera recomendaciones inteligentes por tipo:
     • Descansos preventivos
     • Redistribución de tareas entre equipo
     • Rotación de turnos
   
   💡 Generar: python manage.py generate_recommendations --all

4️⃣  CONSUMO EN FRONTEND:
   - GET /api/recommendations/ - Listar recomendaciones
   - GET /api/recommendations/?type=break - Filtrar por tipo
   - POST /api/recommendations/{id}/apply/ - Marcar como aplicada
   
   - GET /api/alerts/ - Listar alertas de fatiga
   - POST /api/alerts/{id}/resolve/ - Resolver alerta

5️⃣  ENDPOINTS DISPONIBLES:
   
   🔹 Recomendaciones:
   GET    /api/recommendations/          # Listar todas
   GET    /api/recommendations/{id}/     # Ver detalle
   POST   /api/recommendations/{id}/apply/   # Aplicar
   GET    /api/recommendations/stats/    # Estadísticas
   
   🔹 Alertas:
   GET    /api/alerts/                   # Listar todas
   GET    /api/alerts/{id}/              # Ver detalle
   POST   /api/alerts/{id}/resolve/      # Resolver
   GET    /api/alerts/my_alerts/         # Mis alertas (empleado)
   
   🔹 Métricas y Dashboard:
   GET    /api/metrics/                  # Métricas procesadas
   GET    /api/dashboard/overview/       # Dashboard general

📋 COMANDOS ÚTILES:

   # Ver recomendaciones en consola
   python manage.py shell
   >>> from apps.analytics.models import RoutineRecommendation
   >>> for r in RoutineRecommendation.objects.all()[:5]:
   ...     print(f"{r.get_recommendation_type_display()} - {r.employee.get_full_name()}")
   
   # Ver estado del modelo ML
   python manage.py shell
   >>> from apps.analytics.ml_service import FatigueMLService
   >>> ml = FatigueMLService()
   >>> print(ml.get_model_info())
   
   # Generar más datos de prueba
   python SCRIPTS/esp32_simulator.py
   
   # Entrenar modelo ML
   python SCRIPTS/train_ml_model.py
""")

def main():
    """Función principal."""
    print_header("🤖 SISTEMA DE RECOMENDACIONES CON MACHINE LEARNING")
    print("Sistema Inteligente de Detección de Fatiga Laboral")
    print()
    print("Este script configura y verifica el sistema completo de recomendaciones")
    print("basadas en análisis de patrones de fatiga con Machine Learning.")
    
    try:
        # 1. Verificar datos
        has_data = check_database_data()
        
        if not has_data:
            print("\n" + "!" * 80)
            print("⚠️  ADVERTENCIA: Datos insuficientes para análisis confiable")
            print("!" * 80)
            print("\n💡 Sigue estos pasos:")
            print("   1. Ejecuta: python SCRIPTS/esp32_simulator.py (por 2-5 minutos)")
            print("   2. Ejecuta: python manage.py process_metrics")
            print("   3. Vuelve a ejecutar este script")
            print()
            response = input("¿Deseas continuar de todos modos? (s/n): ")
            if response.lower() != 's':
                return
        
        # 2. Verificar modelo ML
        has_ml = check_ml_model()
        
        # 3. Generar recomendaciones
        result = generate_recommendations()
        
        if result['total'] > 0:
            # 4. Mostrar ejemplos
            show_recommendation_examples()
        
        # 5. Resumen del sistema
        show_system_summary()
        
        # 6. Instrucciones de uso
        show_usage_instructions()
        
        # Mensaje final
        print_header("✅ CONFIGURACIÓN COMPLETADA")
        
        if has_ml:
            print("🎉 El sistema está completamente configurado y funcionando con ML")
        else:
            print("⚠️  El sistema funciona pero sin modelo ML entrenado")
            print("💡 Entrena el modelo para mejores predicciones: python SCRIPTS/train_ml_model.py")
        
        print(f"\n📊 Total de recomendaciones disponibles: {result['total']}")
        print("\n🚀 El sistema está listo para usar!")
        print("   Accede a las recomendaciones vía API: /api/recommendations/")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
