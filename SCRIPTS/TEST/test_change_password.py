"""
Script para probar el endpoint de cambio de contraseña.
Verifica que funcione correctamente.
"""

import requests
from colorama import init, Fore, Style

init(autoreset=True)

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.CYAN}ℹ️  {text}{Style.RESET_ALL}")

def test_change_password():
    """Prueba el endpoint de cambio de contraseña"""
    
    BASE_URL = 'http://localhost:8000'
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"🧪 TEST: Cambio de Contraseña")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # 1. Login como admin
    print_info("1. Obteniendo token de autenticación...")
    
    try:
        response = requests.post(f'{BASE_URL}/api/auth/login/', json={
            'email': 'admin@example.com',
            'password': 'admin123'
        })
        
        if response.status_code != 200:
            print_error(f"Login falló: {response.status_code}")
            print(response.text)
            return
        
        token = response.json().get('access')
        print_success(f"Token obtenido")
        
    except Exception as e:
        print_error(f"Error en login: {e}")
        return
    
    # 2. Intentar cambiar contraseña
    print_info("\n2. Probando cambio de contraseña...")
    
    # Test con datos correctos
    print_info("   Test 1: Contraseña actual incorrecta")
    try:
        response = requests.post(
            f'{BASE_URL}/api/auth/change-password/',
            json={
                'old_password': 'wrongpassword',
                'new_password': 'newpassword123',
                'new_password_confirm': 'newpassword123'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if response.status_code == 400:
            print_success(f"   Validación correcta (400): {response.json()}")
        else:
            print_error(f"   Status inesperado: {response.status_code}")
            print(f"   Respuesta: {response.text}")
    
    except Exception as e:
        print_error(f"   Error: {e}")
    
    # Test con contraseñas que no coinciden
    print_info("\n   Test 2: Contraseñas nuevas no coinciden")
    try:
        response = requests.post(
            f'{BASE_URL}/api/auth/change-password/',
            json={
                'old_password': 'admin123',
                'new_password': 'newpassword123',
                'new_password_confirm': 'differentpassword'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if response.status_code == 400:
            print_success(f"   Validación correcta (400): {response.json()}")
        else:
            print_error(f"   Status inesperado: {response.status_code}")
            print(f"   Respuesta: {response.text}")
    
    except Exception as e:
        print_error(f"   Error: {e}")
    
    # Test con contraseña muy corta
    print_info("\n   Test 3: Contraseña muy corta (<8 caracteres)")
    try:
        response = requests.post(
            f'{BASE_URL}/api/auth/change-password/',
            json={
                'old_password': 'admin123',
                'new_password': 'short',
                'new_password_confirm': 'short'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if response.status_code == 400:
            print_success(f"   Validación correcta (400): {response.json()}")
        else:
            print_error(f"   Status inesperado: {response.status_code}")
            print(f"   Respuesta: {response.text}")
    
    except Exception as e:
        print_error(f"   Error: {e}")
    
    # Test con datos faltantes
    print_info("\n   Test 4: Datos faltantes")
    try:
        response = requests.post(
            f'{BASE_URL}/api/auth/change-password/',
            json={
                'old_password': 'admin123'
                # Faltan new_password y new_password_confirm
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if response.status_code == 400:
            print_success(f"   Validación correcta (400): {response.json()}")
        else:
            print_error(f"   Status inesperado: {response.status_code}")
            print(f"   Respuesta: {response.text}")
    
    except Exception as e:
        print_error(f"   Error: {e}")
    
    # Test con objeto vacío (lo que puede estar enviando el frontend)
    print_info("\n   Test 5: Objeto vacío (posible problema del frontend)")
    try:
        response = requests.post(
            f'{BASE_URL}/api/auth/change-password/',
            json={},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if response.status_code == 400:
            print_success(f"   Validación correcta (400): {response.json()}")
            print_error(f"\n   ⚠️  ESTE PUEDE SER EL PROBLEMA DEL FRONTEND")
            print_error(f"   El frontend está enviando un objeto vacío o sin los campos requeridos")
        else:
            print_error(f"   Status inesperado: {response.status_code}")
            print(f"   Respuesta: {response.text}")
    
    except Exception as e:
        print_error(f"   Error: {e}")
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}📋 CAMPOS REQUERIDOS POR EL BACKEND:{Style.RESET_ALL}")
    print(f"""
    {{
        "old_password": "contraseña_actual",      // required
        "new_password": "nueva_contraseña",       // required, min 8 chars
        "new_password_confirm": "nueva_contraseña" // required, min 8 chars
    }}
    """)
    
    print(f"\n{Fore.YELLOW}🔍 VERIFICAR EN EL FRONTEND:{Style.RESET_ALL}")
    print(f"""
    1. Que los inputs tengan los nombres correctos
    2. Que se estén enviando los 3 campos
    3. Que el Content-Type sea 'application/json'
    4. Que el token JWT esté en el header
    """)

if __name__ == '__main__':
    try:
        test_change_password()
    except KeyboardInterrupt:
        print("\n\nTest interrumpido")
    except Exception as e:
        print_error(f"Error general: {e}")
