"""
Script para probar el endpoint de exportación de datos del empleado.
Ejecutar desde el directorio del backend: python SCRIPTS/TEST/test_employee_export_data.py
"""
import os
import sys
import requests

# Configurar el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configuración
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
EXPORT_URL = f"{BASE_URL}/api/auth/employee/export-my-data/"

# Credenciales de prueba (ajusta según tu BD)
EMPLOYEE_EMAIL = "sisac@gmail.com"  # Cambiar por un empleado real
EMPLOYEE_PASSWORD = "123456"  # Cambiar por la contraseña real

def test_employee_export():
    print("=" * 70)
    print("PRUEBA: EXPORTAR DATOS DEL EMPLEADO")
    print("=" * 70)
    
    # 1. Login del empleado
    print("\n1️⃣  Iniciando sesión como empleado...")
    login_data = {
        "email": EMPLOYEE_EMAIL,
        "password": EMPLOYEE_PASSWORD
    }
    
    try:
        login_response = requests.post(LOGIN_URL, json=login_data)
        login_response.raise_for_status()
        tokens = login_response.json()
        access_token = tokens.get('access')
        
        if not access_token:
            print("❌ Error: No se obtuvo el token de acceso")
            return
        
        print(f"✅ Sesión iniciada correctamente")
        print(f"   Token: {access_token[:20]}...")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al iniciar sesión: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Respuesta del servidor: {e.response.text}")
        return
    
    # 2. Exportar datos del empleado
    print("\n2️⃣  Descargando datos del empleado...")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        export_response = requests.get(EXPORT_URL, headers=headers)
        export_response.raise_for_status()
        
        # Guardar el archivo
        filename = f"datos_empleado_test_{EMPLOYEE_EMAIL.split('@')[0]}.xlsx"
        output_path = os.path.join(os.path.dirname(__file__), filename)
        
        with open(output_path, 'wb') as f:
            f.write(export_response.content)
        
        file_size = len(export_response.content)
        print(f"✅ Archivo descargado exitosamente")
        print(f"   Ubicación: {output_path}")
        print(f"   Tamaño: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        print(f"   Content-Type: {export_response.headers.get('Content-Type')}")
        
        # Verificar que es un archivo Excel válido
        if export_response.headers.get('Content-Type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            print("✅ El archivo tiene el formato correcto (Excel .xlsx)")
        else:
            print("⚠️  Advertencia: El Content-Type no es el esperado")
        
        print("\n" + "=" * 70)
        print("✅ PRUEBA EXITOSA")
        print("=" * 70)
        print(f"\n📄 Puedes abrir el archivo en Excel para verificar el contenido:")
        print(f"   {output_path}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al exportar datos: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Respuesta del servidor: {e.response.text[:500]}")
        return

if __name__ == "__main__":
    test_employee_export()
