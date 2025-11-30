"""
Script para probar endpoints del sistema sin modificar nada.
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_result(title, response):
    """Imprime el resultado de una petición."""
    print("\n" + "="*70)
    print(f"🧪 {title}")
    print("="*70)
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(response.text)
    print("="*70)

def test_login(email, password):
    """Prueba el login y retorna el token."""
    print(f"\n🔐 Probando login con: {email}")
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json={"email": email, "password": password}
    )
    print_result(f"Login - {email}", response)
    if response.status_code == 200:
        return response.json().get('access')
    return None

def test_current_user(token):
    """Prueba el endpoint de usuario actual."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me/", headers=headers)
    print_result("Usuario Actual (GET /api/auth/me/)", response)

def test_admin_stats(token):
    """Prueba estadísticas de admin."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/admin/stats/", headers=headers)
    print_result("Estadísticas Admin (GET /api/admin/stats/)", response)

def test_list_devices(token):
    """Lista todos los dispositivos."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/devices/", headers=headers)
    print_result("Lista de Dispositivos (GET /api/devices/)", response)

def test_list_alerts(token):
    """Lista todas las alertas."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/alerts/", headers=headers)
    print_result("Lista de Alertas (GET /api/alerts/)", response)

def test_list_recommendations(token):
    """Lista todas las recomendaciones."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/recommendations/", headers=headers)
    print_result("Recomendaciones (GET /api/recommendations/)", response)

def test_dashboard_summary(token):
    """Prueba el resumen del dashboard."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/dashboard/summary/", headers=headers)
    print_result("Dashboard Summary (GET /api/dashboard/summary/)", response)

def test_sensor_data(token):
    """Lista datos de sensores."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/sensor-data/?limit=5", headers=headers)
    print_result("Datos de Sensores (GET /api/sensor-data/)", response)

def test_processed_metrics(token):
    """Lista métricas procesadas."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/processed-metrics/?limit=5", headers=headers)
    print_result("Métricas Procesadas (GET /api/processed-metrics/)", response)

def main():
    print("\n" + "🚀"*35)
    print("PRUEBA DE ENDPOINTS - SISTEMA DE MONITOREO DE FATIGA")
    print("🚀"*35)
    print(f"\n⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Probar login con ADMIN
    admin_token = test_login("admin@example.com", "admin123")
    
    if not admin_token:
        print("\n❌ Login falló. Deteniendo pruebas.")
        return
    
    print("\n✅ Login exitoso. Token obtenido.")
    
    # 2. Probar endpoints con el token de admin
    test_current_user(admin_token)
    test_admin_stats(admin_token)
    test_list_devices(admin_token)
    test_list_alerts(admin_token)
    test_list_recommendations(admin_token)
    test_dashboard_summary(admin_token)
    test_sensor_data(admin_token)
    test_processed_metrics(admin_token)
    
    # 3. Probar login con SUPERVISOR
    print("\n" + "🔄"*35)
    print("PROBANDO CON SUPERVISOR")
    print("🔄"*35)
    supervisor_token = test_login("supervisor@example.com", "super123")
    
    if supervisor_token:
        test_current_user(supervisor_token)
        test_dashboard_summary(supervisor_token)
        test_list_alerts(supervisor_token)
    
    # 4. Probar login con EMPLEADO
    print("\n" + "🔄"*35)
    print("PROBANDO CON EMPLEADO")
    print("🔄"*35)
    employee_token = test_login("employee1@example.com", "emp123")
    
    if employee_token:
        test_current_user(employee_token)
        test_dashboard_summary(employee_token)
    
    print("\n" + "✅"*35)
    print("PRUEBA DE ENDPOINTS COMPLETADA")
    print("✅"*35)

if __name__ == "__main__":
    main()
