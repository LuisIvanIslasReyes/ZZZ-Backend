"""
Script para probar que el contador de síntomas pendientes se actualiza correctamente
después de marcar un síntoma como revisado.

Flujo:
1. Login como supervisor
2. Obtener conteo inicial de pendientes
3. Revisar un síntoma pendiente
4. Verificar que el conteo disminuyó
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def login(email, password):
    """Obtener token de autenticación."""
    response = requests.post(f"{BASE_URL}/auth/login/", json={
        'email': email,
        'password': password
    })
    
    if response.status_code == 200:
        data = response.json()
        return data['access']
    else:
        print(f"❌ Error login: {response.status_code}")
        print(response.text)
        return None

def get_pending_count(token):
    """Obtener contador de síntomas pendientes."""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/symptom-reports/pending-count/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data['count'], data
    else:
        print(f"❌ Error pending-count: {response.status_code}")
        print(response.text)
        return None, None

def get_pending_list(token):
    """Obtener lista de síntomas pendientes."""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/symptom-reports/pending/", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error pending list: {response.status_code}")
        print(response.text)
        return []

def review_symptom(token, symptom_id, notes="Revisado - Test automático"):
    """Marcar síntoma como revisado."""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(
        f"{BASE_URL}/symptom-reports/{symptom_id}/review/",
        json={'notes': notes},
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error review: {response.status_code}")
        print(response.text)
        return None

def main():
    print("=" * 60)
    print("🧪 TEST: Actualización de Contador de Síntomas Pendientes")
    print("=" * 60)
    
    # Credenciales del supervisor
    SUPERVISOR_EMAIL = input("Email del supervisor: ").strip() or "supervisor@empresa.com"
    SUPERVISOR_PASSWORD = input("Password: ").strip() or "password123"
    
    print("\n1️⃣ Login como supervisor...")
    token = login(SUPERVISOR_EMAIL, SUPERVISOR_PASSWORD)
    if not token:
        print("❌ No se pudo autenticar")
        sys.exit(1)
    print("✅ Login exitoso")
    
    print("\n2️⃣ Obteniendo conteo inicial de pendientes...")
    initial_count, initial_data = get_pending_count(token)
    if initial_count is None:
        print("❌ No se pudo obtener el conteo")
        sys.exit(1)
    
    print(f"✅ Conteo inicial: {initial_count}")
    print(f"   Por severidad: {json.dumps(initial_data['by_severity'], indent=2)}")
    
    if initial_count == 0:
        print("\n⚠️  No hay síntomas pendientes para probar")
        print("   Crea un síntoma desde el frontend primero")
        sys.exit(0)
    
    print("\n3️⃣ Obteniendo lista de síntomas pendientes...")
    pending_list = get_pending_list(token)
    if not pending_list:
        print("❌ No se pudo obtener la lista")
        sys.exit(1)
    
    first_symptom = pending_list[0]
    symptom_id = first_symptom['id']
    print(f"✅ Síntoma seleccionado:")
    print(f"   ID: {symptom_id}")
    print(f"   Tipo: {first_symptom['symptom_type']}")
    print(f"   Severidad: {first_symptom['severity']}")
    print(f"   Empleado: {first_symptom.get('employee', {}).get('full_name', 'N/A')}")
    
    print(f"\n4️⃣ Revisando síntoma ID {symptom_id}...")
    review_result = review_symptom(token, symptom_id)
    if not review_result:
        print("❌ No se pudo revisar el síntoma")
        sys.exit(1)
    print("✅ Síntoma revisado exitosamente")
    
    print("\n5️⃣ Obteniendo conteo actualizado...")
    import time
    time.sleep(0.5)  # Pequeña pausa para asegurar commit
    
    final_count, final_data = get_pending_count(token)
    if final_count is None:
        print("❌ No se pudo obtener el conteo actualizado")
        sys.exit(1)
    
    print(f"✅ Conteo final: {final_count}")
    print(f"   Por severidad: {json.dumps(final_data['by_severity'], indent=2)}")
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO:")
    print("=" * 60)
    print(f"Conteo inicial:  {initial_count}")
    print(f"Conteo final:    {final_count}")
    print(f"Diferencia:      {initial_count - final_count}")
    
    if final_count == initial_count - 1:
        print("\n✅ ¡TEST EXITOSO! El contador se actualizó correctamente")
        print("   El endpoint /pending-count/ refleja el cambio inmediatamente")
    elif final_count == initial_count:
        print("\n❌ ¡TEST FALLIDO! El contador NO se actualizó")
        print("   El endpoint sigue devolviendo el mismo valor")
        print("\n🔍 Posibles causas:")
        print("   1. El síntoma no se guardó en la base de datos")
        print("   2. Hay un problema con el filtro is_reviewed=False")
        print("   3. Transacción no commiteada")
    else:
        print(f"\n⚠️  Resultado inesperado: diferencia de {initial_count - final_count}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
