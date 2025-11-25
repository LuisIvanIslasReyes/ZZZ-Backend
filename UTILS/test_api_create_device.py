"""
Script para probar la API de creación de dispositivos.
"""
import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/devices/"

def get_auth_token():
    """Obtener token de autenticación."""
    login_url = f"{BASE_URL}/api/users/login/"
    
    # Intentar con varios usuarios admin/supervisor
    credentials = [
        {"email": "admin@ejemplo.com", "password": "admin123"},
        {"email": "supervisor@ejemplo.com", "password": "super123"},
        {"email": "admin@gmail.com", "password": "admin123"},
    ]
    
    for cred in credentials:
        try:
            response = requests.post(login_url, json=cred)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Autenticado como: {cred['email']}")
                return data.get('access')
        except Exception as e:
            print(f"❌ Error con {cred['email']}: {e}")
    
    print("❌ No se pudo autenticar con ningún usuario")
    return None

def get_employees(token):
    """Obtener lista de empleados."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/users/", headers=headers)
    
    if response.status_code == 200:
        users = response.json()
        # Buscar empleado8@gmail.com
        for user in users:
            if user.get('email') == 'empleado8@gmail.com':
                return user
    return None

def create_device(token, employee_id):
    """Crear dispositivo."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    device_data = {
        "device_identifier": "ESP32-02",
        "employee": employee_id,
        "is_active": True
    }
    
    print(f"\n🔨 Creando dispositivo...")
    print(f"URL: {API_URL}")
    print(f"Datos: {json.dumps(device_data, indent=2)}")
    
    try:
        response = requests.post(API_URL, json=device_data, headers=headers)
        
        print(f"\n📡 Respuesta del servidor:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            print(f"Body: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Body (raw): {response.text}")
        
        if response.status_code == 201:
            print("\n✅ Dispositivo creado exitosamente!")
            return response.json()
        else:
            print(f"\n❌ Error al crear dispositivo")
            return None
            
    except Exception as e:
        print(f"\n❌ Error en la petición: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*60)
    print("TEST DE CREACIÓN DE DISPOSITIVO VÍA API")
    print("="*60)
    
    # 1. Autenticar
    token = get_auth_token()
    if not token:
        return
    
    # 2. Obtener empleado
    employee = get_employees(token)
    if not employee:
        print("❌ No se encontró el empleado empleado8@gmail.com")
        return
    
    print(f"\n✅ Empleado encontrado:")
    print(f"   ID: {employee.get('id')}")
    print(f"   Nombre: {employee.get('first_name')} {employee.get('last_name')}")
    print(f"   Email: {employee.get('email')}")
    
    # 3. Crear dispositivo
    device = create_device(token, employee.get('id'))
    
    if device:
        print(f"\n{'='*60}")
        print("✅ PRUEBA EXITOSA")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("❌ PRUEBA FALLIDA")
        print(f"{'='*60}")

if __name__ == '__main__':
    main()
