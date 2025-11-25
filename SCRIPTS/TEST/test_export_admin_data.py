"""
Script de prueba para el endpoint de exportación de datos del administrador.
Ejecutar después de iniciar el servidor Django.

Para usar:
1. Asegúrate de tener un usuario admin creado
2. python SCRIPTS/TEST/test_export_admin_data.py
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

def test_export_admin_data():
    print("=" * 80)
    print("TEST: EXPORTACIÓN DE DATOS DEL ADMINISTRADOR")
    print("=" * 80)
    print()
    
    # 1. Login
    print("1️⃣  Iniciando sesión como administrador...")
    login_url = f"{BASE_URL}/auth/login/"
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        tokens = response.json()
        access_token = tokens['access']
        print(f"   ✅ Login exitoso")
        print(f"   Token: {access_token[:50]}...")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error en login: {e}")
        return
    
    print()
    
    # 2. Exportar datos
    print("2️⃣  Exportando datos personales...")
    export_url = f"{BASE_URL}/admin/export-my-data/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(export_url, headers=headers)
        response.raise_for_status()
        
        # Verificar que sea un CSV
        content_type = response.headers.get('Content-Type')
        content_disposition = response.headers.get('Content-Disposition')
        
        print(f"   ✅ Datos exportados correctamente")
        print(f"   Content-Type: {content_type}")
        print(f"   Content-Disposition: {content_disposition}")
        print(f"   Tamaño del archivo: {len(response.content)} bytes")
        
        # Guardar archivo
        filename = "mis_datos_test.csv"
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"   📄 Archivo guardado como: {filename}")
        print()
        
        # Mostrar primeras líneas
        print("3️⃣  Primeras líneas del CSV:")
        print("-" * 80)
        lines = response.content.decode('utf-8-sig').split('\n')[:15]
        for line in lines:
            print(f"   {line}")
        print("   ...")
        print("-" * 80)
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error al exportar: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Respuesta: {e.response.text}")
        return
    
    print()
    print("=" * 80)
    print("✅ TEST COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    test_export_admin_data()
