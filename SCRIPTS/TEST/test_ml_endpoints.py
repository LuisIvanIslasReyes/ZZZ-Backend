"""
Script para probar los endpoints del Dashboard de ML.
Verifica que todos los endpoints respondan correctamente.
"""

import sys
import os
import django

# Configurar Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import requests
from colorama import init, Fore, Style
from apps.users.models import User

init(autoreset=True)

def print_header(text):
    """Imprime encabezado colorido"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def print_success(text):
    """Imprime mensaje de éxito"""
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    """Imprime mensaje de error"""
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_info(text):
    """Imprime mensaje informativo"""
    print(f"{Fore.YELLOW}ℹ️  {text}{Style.RESET_ALL}")

def print_data(label, value):
    """Imprime par clave-valor"""
    print(f"  {Fore.WHITE}{label}:{Style.RESET_ALL} {value}")

def get_auth_token():
    """Obtiene token de autenticación"""
    try:
        # Buscar usuario admin
        admin = User.objects.filter(role='admin').first()
        if not admin:
            print_error("No se encontró usuario admin")
            return None
        
        # Login
        response = requests.post('http://localhost:8000/api/auth/login/', json={
            'email': admin.email,
            'password': 'admin123'  # Asume contraseña por defecto
        })
        
        if response.status_code == 200:
            token = response.json().get('access')
            print_success(f"Token obtenido para {admin.email}")
            return token
        else:
            print_error(f"No se pudo obtener token: {response.status_code}")
            return None
    
    except Exception as e:
        print_error(f"Error al obtener token: {e}")
        return None

def test_endpoint(name, url, token, method='GET', data=None):
    """Prueba un endpoint"""
    print_info(f"Probando: {name}")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data or {})
        else:
            print_error(f"Método no soportado: {method}")
            return False
        
        print_data("Status", response.status_code)
        
        if response.status_code in [200, 202]:
            print_success(f"{name} funcionando correctamente")
            
            # Mostrar datos relevantes
            try:
                json_data = response.json()
                if name == "Model Info":
                    print_data("  Modelo existe", json_data.get('model_exists'))
                    print_data("  Tipo", json_data.get('ml_service', {}).get('type'))
                    print_data("  Características", json_data.get('ml_service', {}).get('features_count'))
                    print_data("  Muestras entrenamiento", json_data.get('training', {}).get('samples'))
                    print_data("  Fecha entrenamiento", json_data.get('training', {}).get('date'))
                
                elif name == "Statistics":
                    print_data("  Total predicciones", json_data.get('predictions', {}).get('total'))
                    print_data("  Últimas 24h", json_data.get('predictions', {}).get('last_24h'))
                    print_data("  Fatiga promedio", f"{json_data.get('predictions', {}).get('average_fatigue', 0):.2f}%")
                
                elif name == "Retraining Status":
                    print_data("  Último entrenamiento", json_data.get('last_training'))
                    print_data("  Próximo automático", json_data.get('next_scheduled'))
                    print_data("  Datos disponibles", json_data.get('available_metrics'))
                    print_data("  Puede re-entrenar", json_data.get('can_retrain'))
                
                elif name == "Prediction History":
                    print_data("  Total registros", json_data.get('count'))
                    if json_data.get('predictions'):
                        first_pred = json_data['predictions'][0]
                        print_data("  Último dispositivo", first_pred.get('device'))
                        print_data("  Último empleado", first_pred.get('employee'))
                        print_data("  Última fatiga", f"{first_pred.get('fatigue_index')}%")
                
            except Exception as e:
                print_info(f"  Datos JSON: {str(e)}")
            
            return True
        
        elif response.status_code == 400:
            print_error(f"{name} - Error 400: {response.json()}")
            return False
        
        elif response.status_code == 403:
            print_error(f"{name} - Sin permisos")
            return False
        
        elif response.status_code == 404:
            print_error(f"{name} - No encontrado")
            return False
        
        else:
            print_error(f"{name} - Error {response.status_code}")
            try:
                print_info(f"  Respuesta: {response.json()}")
            except:
                print_info(f"  Respuesta: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print_error(f"No se pudo conectar a {url}")
        print_info("Verifica que el servidor Django esté corriendo (python manage.py runserver)")
        return False
    
    except Exception as e:
        print_error(f"Error al probar {name}: {e}")
        return False

def main():
    """Función principal"""
    print_header("🧪 TEST DE ENDPOINTS ML DASHBOARD")
    
    BASE_URL = 'http://localhost:8000'
    
    # Obtener token
    print_header("1. AUTENTICACIÓN")
    token = get_auth_token()
    
    if not token:
        print_error("No se pudo obtener token de autenticación")
        print_info("Asegúrate de tener un usuario admin con contraseña 'admin123'")
        return
    
    # Probar endpoints GET
    print_header("2. ENDPOINTS GET")
    
    results = []
    
    results.append(test_endpoint(
        "Model Info",
        f"{BASE_URL}/api/ml/model-info/",
        token
    ))
    
    results.append(test_endpoint(
        "Statistics",
        f"{BASE_URL}/api/ml/statistics/",
        token
    ))
    
    results.append(test_endpoint(
        "Retraining Status",
        f"{BASE_URL}/api/ml/retraining/",
        token
    ))
    
    results.append(test_endpoint(
        "Prediction History",
        f"{BASE_URL}/api/ml/predictions/history/?limit=5",
        token
    ))
    
    # Resumen
    print_header("3. RESUMEN")
    total = len(results)
    passed = sum(results)
    
    print(f"\n{Fore.WHITE}Total endpoints probados: {total}")
    print(f"{Fore.GREEN}Exitosos: {passed}")
    print(f"{Fore.RED}Fallidos: {total - passed}{Style.RESET_ALL}\n")
    
    if passed == total:
        print_success("🎉 TODOS LOS ENDPOINTS FUNCIONAN CORRECTAMENTE")
    else:
        print_error("⚠️ ALGUNOS ENDPOINTS TIENEN PROBLEMAS")
    
    # Información adicional
    print_header("4. PRÓXIMOS PASOS")
    print("1. Implementar componentes frontend según FRONTEND_ML_DASHBOARD.md")
    print("2. Integrar endpoints en el frontend")
    print("3. Probar flujo de re-entrenamiento manual")
    print("4. Agregar visualizaciones (clustering_analysis.png)")
    print("5. Implementar auto-refresh en frontend")
    print()

if __name__ == '__main__':
    main()
