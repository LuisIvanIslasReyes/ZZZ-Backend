"""
Pruebas de Funcionalidad del Backend
Sistema de Detección de Fatiga - API REST

Este script prueba todos los endpoints del backend y genera evidencias automáticas.
"""
import requests
import json
from datetime import datetime
from pathlib import Path
import time

# Configuración
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"
AUTH_URL = f"{BASE_URL}/api/auth"

# Credenciales de prueba
TEST_USER = {
    "email": "admin@example.com",
    "password": "admin123"
}

class BackendFunctionalTester:
    def __init__(self):
        self.results = []
        self.token = None
        self.headers = {}
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        
    def log_result(self, category, test_name, description, success, status_code=None, 
                   response_data=None, error=None, request_info=None):
        """Registra el resultado de una prueba"""
        self.test_count += 1
        if success:
            self.passed_count += 1
        else:
            self.failed_count += 1
            
        result = {
            "id": self.test_count,
            "category": category,
            "test": test_name,
            "description": description,
            "success": success,
            "status_code": status_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "response_data": response_data,
            "request_info": request_info,
            "error": str(error) if error else None
        }
        self.results.append(result)
        
        # Mostrar en consola
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} [{self.test_count}] {test_name}")
        print(f"   {description}")
        if status_code:
            print(f"   Status: {status_code}")
        if error:
            print(f"   Error: {error}")
        print()
        
    def authenticate(self):
        """Obtener token de autenticación"""
        try:
            response = requests.post(
                f"{AUTH_URL}/login/",
                json=TEST_USER,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                self.headers = {"Authorization": f"Bearer {self.token}"}
                return True
            return False
        except Exception as e:
            print(f"⚠️  Error en autenticación: {e}")
            return False
    
    # ==================== CATEGORÍA: AUTENTICACIÓN ====================
    
    def test_auth_login_success(self):
        """PF-001: Login exitoso con credenciales válidas"""
        try:
            response = requests.post(
                f"{AUTH_URL}/login/",
                json=TEST_USER,
                timeout=10
            )
            
            response_data = None
            if response.status_code == 200:
                data = response.json()
                response_data = {
                    "has_access_token": bool(data.get('access')),
                    "has_refresh_token": bool(data.get('refresh')),
                    "user_data": bool(data.get('user'))
                }
            
            self.log_result(
                "Autenticación",
                "Login Exitoso",
                "Verifica que un usuario puede autenticarse con credenciales válidas",
                response.status_code == 200,
                response.status_code,
                response_data,
                request_info={"endpoint": "/api/auth/login/", "method": "POST"}
            )
        except Exception as e:
            self.log_result("Autenticación", "Login Exitoso", "Login con credenciales válidas", False, error=e)
    
    def test_auth_login_invalid(self):
        """PF-002: Login con credenciales inválidas debe fallar"""
        try:
            response = requests.post(
                f"{AUTH_URL}/login/",
                json={"email": "invalido@test.com", "password": "wrongpass"},
                timeout=10
            )
            
            self.log_result(
                "Autenticación",
                "Login con Credenciales Inválidas",
                "Verifica que se rechacen credenciales incorrectas (esperado: 400 o 401)",
                response.status_code in [400, 401],
                response.status_code,
                request_info={"endpoint": "/api/auth/login/", "method": "POST"}
            )
        except Exception as e:
            self.log_result("Autenticación", "Login Inválido", "Rechazo de credenciales incorrectas", False, error=e)
    
    def test_auth_login_missing_fields(self):
        """PF-003: Login sin campos requeridos debe fallar"""
        try:
            response = requests.post(
                f"{AUTH_URL}/login/",
                json={},
                timeout=10
            )
            
            self.log_result(
                "Autenticación",
                "Login sin Campos Requeridos",
                "Verifica validación de campos obligatorios (esperado: 400)",
                response.status_code == 400,
                response.status_code,
                request_info={"endpoint": "/api/auth/login/", "method": "POST"}
            )
        except Exception as e:
            self.log_result("Autenticación", "Login sin Campos", "Validación de campos", False, error=e)
    
    # ==================== CATEGORÍA: DISPOSITIVOS ====================
    
    def test_devices_list(self):
        """PF-004: Listar todos los dispositivos"""
        try:
            response = requests.get(
                f"{API_URL}/devices/",
                headers=self.headers,
                timeout=10
            )
            
            response_data = None
            if response.status_code == 200:
                data = response.json()
                response_data = {
                    "total_devices": data.get('count', len(data) if isinstance(data, list) else 0),
                    "has_results": bool(data)
                }
            
            self.log_result(
                "Dispositivos",
                "Listar Dispositivos",
                "Obtiene la lista completa de dispositivos registrados",
                response.status_code == 200,
                response.status_code,
                response_data,
                request_info={"endpoint": "/api/devices/", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Dispositivos", "Listar Dispositivos", "GET /api/devices/", False, error=e)
    
    def test_devices_filter_active(self):
        """PF-005: Filtrar dispositivos activos"""
        try:
            response = requests.get(
                f"{API_URL}/devices/?is_active=true",
                headers=self.headers,
                timeout=10
            )
            
            response_data = None
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', len(data) if isinstance(data, list) else 0)
                response_data = {"active_devices": count}
            
            self.log_result(
                "Dispositivos",
                "Filtrar Dispositivos Activos",
                "Filtra dispositivos por estado activo usando query params",
                response.status_code == 200,
                response.status_code,
                response_data,
                request_info={"endpoint": "/api/devices/?is_active=true", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Dispositivos", "Filtrar Activos", "GET con filtros", False, error=e)
    
    def test_devices_unauthorized(self):
        """PF-006: Acceso a dispositivos sin autenticación debe fallar"""
        try:
            response = requests.get(
                f"{API_URL}/devices/",
                timeout=10
            )
            
            self.log_result(
                "Dispositivos",
                "Acceso sin Autenticación",
                "Verifica que se requiera token JWT (esperado: 401)",
                response.status_code == 401,
                response.status_code,
                request_info={"endpoint": "/api/devices/", "method": "GET", "auth": "none"}
            )
        except Exception as e:
            self.log_result("Dispositivos", "Sin Auth", "GET sin token", False, error=e)
    
    # ==================== CATEGORÍA: DATOS DE SENSORES ====================
    
    def test_sensor_data_list(self):
        """PF-007: Listar datos de sensores"""
        try:
            response = requests.get(
                f"{API_URL}/sensor-data/",
                headers=self.headers,
                timeout=10
            )
            
            response_data = None
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', len(data) if isinstance(data, list) else 0)
                response_data = {"total_records": count}
            
            self.log_result(
                "Datos de Sensores",
                "Listar Datos de Sensores",
                "Obtiene todos los registros de datos de sensores",
                response.status_code == 200,
                response.status_code,
                response_data,
                request_info={"endpoint": "/api/sensor-data/", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Sensores", "Listar Datos", "GET /api/sensor-data/", False, error=e)
    
    def test_sensor_data_ordering(self):
        """PF-008: Ordenar datos por fecha descendente"""
        try:
            response = requests.get(
                f"{API_URL}/sensor-data/?ordering=-timestamp",
                headers=self.headers,
                timeout=10
            )
            
            self.log_result(
                "Datos de Sensores",
                "Ordenar por Fecha (DESC)",
                "Ordena los datos de sensores por timestamp descendente",
                response.status_code == 200,
                response.status_code,
                request_info={"endpoint": "/api/sensor-data/?ordering=-timestamp", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Sensores", "Ordenar Datos", "GET con ordering", False, error=e)
    
    def test_sensor_data_pagination(self):
        """PF-009: Paginación de datos de sensores"""
        try:
            response = requests.get(
                f"{API_URL}/sensor-data/?page=1&page_size=10",
                headers=self.headers,
                timeout=10
            )
            
            response_data = None
            if response.status_code == 200:
                data = response.json()
                response_data = {
                    "has_pagination": 'count' in data or 'next' in data,
                    "page_size": len(data.get('results', data)) if isinstance(data, dict) else len(data)
                }
            
            self.log_result(
                "Datos de Sensores",
                "Paginación",
                "Verifica que la paginación funcione correctamente",
                response.status_code == 200,
                response.status_code,
                response_data,
                request_info={"endpoint": "/api/sensor-data/?page=1&page_size=10", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Sensores", "Paginación", "GET con paginación", False, error=e)
    
    # ==================== CATEGORÍA: MÉTRICAS PROCESADAS ====================
    
    def test_processed_metrics_list(self):
        """PF-010: Listar métricas procesadas"""
        try:
            response = requests.get(
                f"{API_URL}/processed-metrics/",
                headers=self.headers,
                timeout=10
            )
            
            response_data = None
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', len(data) if isinstance(data, list) else 0)
                response_data = {"total_metrics": count}
            
            self.log_result(
                "Métricas Procesadas",
                "Listar Métricas",
                "Obtiene todas las métricas calculadas por el sistema",
                response.status_code == 200,
                response.status_code,
                response_data,
                request_info={"endpoint": "/api/processed-metrics/", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Métricas", "Listar Métricas", "GET /api/processed-metrics/", False, error=e)
    
    def test_processed_metrics_filter(self):
        """PF-011: Filtrar métricas por nivel de actividad"""
        try:
            response = requests.get(
                f"{API_URL}/processed-metrics/?activity_level=high",
                headers=self.headers,
                timeout=10
            )
            
            self.log_result(
                "Métricas Procesadas",
                "Filtrar por Nivel de Actividad",
                "Filtra métricas con nivel de actividad alto",
                response.status_code == 200,
                response.status_code,
                request_info={"endpoint": "/api/processed-metrics/?activity_level=high", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Métricas", "Filtrar Nivel", "GET con filtro", False, error=e)
    
    # ==================== CATEGORÍA: ALERTAS ====================
    
    def test_alerts_list(self):
        """PF-012: Listar alertas de fatiga"""
        try:
            response = requests.get(
                f"{API_URL}/alerts/",
                headers=self.headers,
                timeout=10
            )
            
            response_data = None
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', len(data) if isinstance(data, list) else 0)
                response_data = {"total_alerts": count}
            
            self.log_result(
                "Alertas",
                "Listar Alertas",
                "Obtiene todas las alertas de fatiga generadas",
                response.status_code == 200,
                response.status_code,
                response_data,
                request_info={"endpoint": "/api/alerts/", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Alertas", "Listar Alertas", "GET /api/alerts/", False, error=e)
    
    def test_alerts_filter_active(self):
        """PF-013: Filtrar alertas activas"""
        try:
            response = requests.get(
                f"{API_URL}/alerts/?is_active=true",
                headers=self.headers,
                timeout=10
            )
            
            self.log_result(
                "Alertas",
                "Filtrar Alertas Activas",
                "Obtiene solo las alertas que están actualmente activas",
                response.status_code == 200,
                response.status_code,
                request_info={"endpoint": "/api/alerts/?is_active=true", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Alertas", "Filtrar Activas", "GET con filtro", False, error=e)
    
    # ==================== CATEGORÍA: RECOMENDACIONES ====================
    
    def test_recommendations_list(self):
        """PF-014: Listar recomendaciones"""
        try:
            response = requests.get(
                f"{API_URL}/recommendations/",
                headers=self.headers,
                timeout=10
            )
            
            response_data = None
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', len(data) if isinstance(data, list) else 0)
                response_data = {"total_recommendations": count}
            
            self.log_result(
                "Recomendaciones",
                "Listar Recomendaciones",
                "Obtiene todas las recomendaciones generadas por el sistema",
                response.status_code == 200,
                response.status_code,
                response_data,
                request_info={"endpoint": "/api/recommendations/", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Recomendaciones", "Listar", "GET /api/recommendations/", False, error=e)
    
    def test_recommendations_filter_type(self):
        """PF-015: Filtrar recomendaciones por tipo"""
        try:
            response = requests.get(
                f"{API_URL}/recommendations/?type=break",
                headers=self.headers,
                timeout=10
            )
            
            self.log_result(
                "Recomendaciones",
                "Filtrar por Tipo",
                "Filtra recomendaciones de tipo 'break' (descanso)",
                response.status_code == 200,
                response.status_code,
                request_info={"endpoint": "/api/recommendations/?type=break", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Recomendaciones", "Filtrar Tipo", "GET con filtro", False, error=e)
    
    # ==================== CATEGORÍA: DOCUMENTACIÓN ====================
    
    def test_api_schema(self):
        """PF-016: Schema OpenAPI disponible"""
        try:
            response = requests.get(
                f"{API_URL}/schema/",
                timeout=10
            )
            
            self.log_result(
                "Documentación",
                "Schema OpenAPI",
                "Verifica que el schema de la API esté disponible",
                response.status_code == 200,
                response.status_code,
                request_info={"endpoint": "/api/schema/", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Documentación", "Schema", "GET /api/schema/", False, error=e)
    
    def test_swagger_ui(self):
        """PF-017: Swagger UI disponible"""
        try:
            response = requests.get(
                f"{API_URL}/docs/",
                timeout=10
            )
            
            self.log_result(
                "Documentación",
                "Swagger UI",
                "Verifica que la documentación interactiva esté accesible",
                response.status_code == 200,
                response.status_code,
                request_info={"endpoint": "/api/docs/", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Documentación", "Swagger", "GET /api/docs/", False, error=e)
    
    def test_redoc(self):
        """PF-018: ReDoc disponible"""
        try:
            response = requests.get(
                f"{API_URL}/redoc/",
                timeout=10
            )
            
            self.log_result(
                "Documentación",
                "ReDoc",
                "Verifica que ReDoc esté disponible como documentación alternativa",
                response.status_code == 200,
                response.status_code,
                request_info={"endpoint": "/api/redoc/", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Documentación", "ReDoc", "GET /api/redoc/", False, error=e)
    
    # ==================== CATEGORÍA: MANEJO DE ERRORES ====================
    
    def test_endpoint_not_found(self):
        """PF-019: Endpoint no existente retorna 404"""
        try:
            response = requests.get(
                f"{API_URL}/endpoint-inexistente/",
                headers=self.headers,
                timeout=10
            )
            
            self.log_result(
                "Manejo de Errores",
                "Endpoint No Existente",
                "Verifica que se retorne 404 para rutas inválidas",
                response.status_code == 404,
                response.status_code,
                request_info={"endpoint": "/api/endpoint-inexistente/", "method": "GET"}
            )
        except Exception as e:
            self.log_result("Errores", "404 Not Found", "GET a ruta inválida", False, error=e)
    
    def test_method_not_allowed(self):
        """PF-020: Método HTTP no permitido retorna 405"""
        try:
            # Intentar DELETE en endpoint que solo permite GET
            response = requests.delete(
                f"{API_URL}/devices/",
                headers=self.headers,
                timeout=10
            )
            
            self.log_result(
                "Manejo de Errores",
                "Método No Permitido",
                "Verifica que se retorne 405 para métodos HTTP no soportados",
                response.status_code == 405,
                response.status_code,
                request_info={"endpoint": "/api/devices/", "method": "DELETE"}
            )
        except Exception as e:
            self.log_result("Errores", "405 Method Not Allowed", "DELETE no permitido", False, error=e)
    
    # ==================== EJECUCIÓN PRINCIPAL ====================
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas de funcionalidad"""
        print()
        print("="*70)
        print("PRUEBAS DE FUNCIONALIDAD DEL BACKEND")
        print("Sistema de Detección de Fatiga")
        print("="*70)
        print()
        
        # Autenticación inicial
        print("🔐 Autenticando usuario de prueba...")
        if self.authenticate():
            print("✅ Autenticación exitosa\n")
        else:
            print("⚠️  No se pudo autenticar. Algunas pruebas pueden fallar.\n")
        
        # Ejecutar todas las pruebas por categoría
        print("📋 CATEGORÍA: AUTENTICACIÓN")
        print("-"*70)
        self.test_auth_login_success()
        time.sleep(0.3)
        self.test_auth_login_invalid()
        time.sleep(0.3)
        self.test_auth_login_missing_fields()
        time.sleep(0.3)
        
        print("\n📱 CATEGORÍA: DISPOSITIVOS")
        print("-"*70)
        self.test_devices_list()
        time.sleep(0.3)
        self.test_devices_filter_active()
        time.sleep(0.3)
        self.test_devices_unauthorized()
        time.sleep(0.3)
        
        print("\n📊 CATEGORÍA: DATOS DE SENSORES")
        print("-"*70)
        self.test_sensor_data_list()
        time.sleep(0.3)
        self.test_sensor_data_ordering()
        time.sleep(0.3)
        self.test_sensor_data_pagination()
        time.sleep(0.3)
        
        print("\n📈 CATEGORÍA: MÉTRICAS PROCESADAS")
        print("-"*70)
        self.test_processed_metrics_list()
        time.sleep(0.3)
        self.test_processed_metrics_filter()
        time.sleep(0.3)
        
        print("\n🚨 CATEGORÍA: ALERTAS")
        print("-"*70)
        self.test_alerts_list()
        time.sleep(0.3)
        self.test_alerts_filter_active()
        time.sleep(0.3)
        
        print("\n💡 CATEGORÍA: RECOMENDACIONES")
        print("-"*70)
        self.test_recommendations_list()
        time.sleep(0.3)
        self.test_recommendations_filter_type()
        time.sleep(0.3)
        
        print("\n📚 CATEGORÍA: DOCUMENTACIÓN")
        print("-"*70)
        self.test_api_schema()
        time.sleep(0.3)
        self.test_swagger_ui()
        time.sleep(0.3)
        self.test_redoc()
        time.sleep(0.3)
        
        print("\n⚠️  CATEGORÍA: MANEJO DE ERRORES")
        print("-"*70)
        self.test_endpoint_not_found()
        time.sleep(0.3)
        self.test_method_not_allowed()
        
        # Generar reportes
        self.print_summary()
        self.generate_reports()
    
    def print_summary(self):
        """Imprime resumen de resultados"""
        print()
        print("="*70)
        print("RESUMEN DE PRUEBAS DE FUNCIONALIDAD")
        print("="*70)
        
        success_rate = (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
        
        print(f"Total de pruebas ejecutadas: {self.test_count}")
        print(f"Pruebas exitosas: {self.passed_count} ✅")
        print(f"Pruebas fallidas: {self.failed_count} ❌")
        print(f"Tasa de éxito: {success_rate:.1f}%")
        print("="*70)
    
    def generate_reports(self):
        """Genera reportes HTML y JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generar JSON
        self.generate_json_report(timestamp)
        
        # Generar HTML
        self.generate_html_report(timestamp)
    
    def generate_json_report(self, timestamp):
        """Genera reporte en formato JSON"""
        filename = f"evidencia_funcionalidad_{timestamp}.json"
        output_path = Path(__file__).parent / filename
        
        report_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "backend_url": BASE_URL,
            "total_tests": self.test_count,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "success_rate": round((self.passed_count / self.test_count * 100) if self.test_count > 0 else 0, 2),
            "results": self.results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Reporte JSON generado: {output_path}")
    
    def generate_html_report(self, timestamp):
        """Genera reporte en formato HTML"""
        filename = f"evidencia_funcionalidad_{timestamp}.html"
        output_path = Path(__file__).parent / filename
        
        success_rate = (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
        
        # Agrupar resultados por categoría
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evidencia de Pruebas de Funcionalidad - Backend</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.95;
        }}
        
        .metadata {{
            background: #f8f9fa;
            padding: 20px 40px;
            border-bottom: 3px solid #e9ecef;
        }}
        
        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }}
        
        .metadata-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .metadata-label {{
            font-weight: bold;
            color: #495057;
        }}
        
        .metadata-value {{
            color: #212529;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 25px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .summary-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .summary-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        }}
        
        .summary-card h3 {{
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
        }}
        
        .summary-card .value {{
            font-size: 3em;
            font-weight: bold;
            line-height: 1;
        }}
        
        .summary-card .icon {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .category {{
            margin-bottom: 40px;
        }}
        
        .category-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .category-header h2 {{
            font-size: 1.5em;
        }}
        
        .category-icon {{
            font-size: 2em;
        }}
        
        .test-result {{
            background: white;
            margin-bottom: 20px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
        }}
        
        .test-result:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateX(5px);
        }}
        
        .test-header {{
            padding: 25px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        .test-header.success {{
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border-left: 6px solid #28a745;
        }}
        
        .test-header.failure {{
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border-left: 6px solid #dc3545;
        }}
        
        .test-info {{
            flex: 1;
        }}
        
        .test-id {{
            display: inline-block;
            background: rgba(0,0,0,0.1);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .test-name {{
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 8px;
            color: #212529;
        }}
        
        .test-description {{
            color: #6c757d;
            line-height: 1.6;
        }}
        
        .test-status {{
            font-size: 2.5em;
            flex-shrink: 0;
        }}
        
        .test-details {{
            padding: 25px;
            background: #f8f9fa;
        }}
        
        .detail-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .detail-item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .detail-label {{
            font-weight: bold;
            color: #495057;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        
        .detail-value {{
            color: #212529;
            font-size: 1.1em;
        }}
        
        .code-block {{
            background: #282c34;
            color: #abb2bf;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.6;
            margin-top: 15px;
        }}
        
        .error-box {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            color: #856404;
        }}
        
        .error-box strong {{
            display: block;
            margin-bottom: 8px;
            color: #dc3545;
        }}
        
        .footer {{
            background: #343a40;
            color: white;
            text-align: center;
            padding: 30px;
            margin-top: 40px;
        }}
        
        .footer p {{
            margin: 5px 0;
        }}
        
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            margin: 2px;
        }}
        
        .badge.success {{
            background: #28a745;
            color: white;
        }}
        
        .badge.error {{
            background: #dc3545;
            color: white;
        }}
        
        .badge.info {{
            background: #17a2b8;
            color: white;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
            }}
            
            .test-result {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Pruebas de Funcionalidad del Backend</h1>
            <div class="subtitle">Sistema de Detección de Fatiga - API REST</div>
        </div>
        
        <div class="metadata">
            <div class="metadata-grid">
                <div class="metadata-item">
                    <span class="metadata-label">📅 Fecha:</span>
                    <span class="metadata-value">{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">🌐 Backend URL:</span>
                    <span class="metadata-value">{BASE_URL}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">📊 Total de Pruebas:</span>
                    <span class="metadata-value">{self.test_count}</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">⏱️ Timestamp:</span>
                    <span class="metadata-value">{timestamp}</span>
                </div>
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="icon">📋</div>
                <h3>Total de Pruebas</h3>
                <div class="value" style="color: #667eea;">{self.test_count}</div>
            </div>
            <div class="summary-card">
                <div class="icon">✅</div>
                <h3>Exitosas</h3>
                <div class="value" style="color: #28a745;">{self.passed_count}</div>
            </div>
            <div class="summary-card">
                <div class="icon">❌</div>
                <h3>Fallidas</h3>
                <div class="value" style="color: #dc3545;">{self.failed_count}</div>
            </div>
            <div class="summary-card">
                <div class="icon">📈</div>
                <h3>Tasa de Éxito</h3>
                <div class="value" style="color: {'#28a745' if success_rate >= 80 else '#ffc107' if success_rate >= 60 else '#dc3545'};">
                    {success_rate:.1f}%
                </div>
            </div>
        </div>
        
        <div class="content">
"""
        
        # Generar cada categoría
        category_icons = {
            "Autenticación": "🔐",
            "Dispositivos": "📱",
            "Datos de Sensores": "📊",
            "Métricas Procesadas": "📈",
            "Alertas": "🚨",
            "Recomendaciones": "💡",
            "Documentación": "📚",
            "Manejo de Errores": "⚠️"
        }
        
        for category_name, tests in categories.items():
            icon = category_icons.get(category_name, "📋")
            html_content += f"""
            <div class="category">
                <div class="category-header">
                    <div class="category-icon">{icon}</div>
                    <h2>{category_name}</h2>
                    <span class="badge info">{len(tests)} pruebas</span>
                </div>
"""
            
            for test in tests:
                status_class = "success" if test['success'] else "failure"
                status_icon = "✅" if test['success'] else "❌"
                
                html_content += f"""
                <div class="test-result">
                    <div class="test-header {status_class}">
                        <div class="test-info">
                            <div class="test-id">PF-{test['id']:03d}</div>
                            <div class="test-name">{test['test']}</div>
                            <div class="test-description">{test['description']}</div>
                        </div>
                        <div class="test-status">{status_icon}</div>
                    </div>
                    <div class="test-details">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <div class="detail-label">Timestamp</div>
                                <div class="detail-value">{test['timestamp']}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Status Code</div>
                                <div class="detail-value">
                                    <span class="badge {'success' if test['status_code'] in [200, 201] else 'error' if test['status_code'] >= 400 else 'info'}">
                                        {test['status_code'] or 'N/A'}
                                    </span>
                                </div>
                            </div>
"""
                
                if test.get('request_info'):
                    req = test['request_info']
                    html_content += f"""
                            <div class="detail-item">
                                <div class="detail-label">Endpoint</div>
                                <div class="detail-value">{req.get('endpoint', 'N/A')}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Método HTTP</div>
                                <div class="detail-value"><span class="badge info">{req.get('method', 'N/A')}</span></div>
                            </div>
"""
                
                html_content += """
                        </div>
"""
                
                if test.get('error'):
                    html_content += f"""
                        <div class="error-box">
                            <strong>⚠️ Error:</strong>
                            {test['error']}
                        </div>
"""
                
                if test.get('response_data'):
                    html_content += f"""
                        <div class="code-block">{json.dumps(test['response_data'], indent=2, ensure_ascii=False)}</div>
"""
                
                html_content += """
                    </div>
                </div>
"""
            
            html_content += """
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="footer">
            <p><strong>Sistema de Detección de Fatiga con IoT</strong></p>
            <p>Proyecto: ZZZ-Backend | Django Rest Framework</p>
            <p>Reporte generado automáticamente - {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Reporte HTML generado: {output_path}")
        print()

if __name__ == "__main__":
    print()
    print("🚀 Iniciando Pruebas de Funcionalidad del Backend")
    print("   Sistema de Detección de Fatiga")
    print()
    
    tester = BackendFunctionalTester()
    tester.run_all_tests()
    
    print()
    print("✅ Pruebas completadas. Revisa los archivos de evidencia generados.")
    print()
