import requests
import time

print("Esperando que el servidor esté listo...")
time.sleep(2)

BASE_URL = "http://localhost:8000/api"

# Test 1: Login
print("\n✅ TEST 1: Login Admin")
response = requests.post(f"{BASE_URL}/auth/login/", json={
    "email": "admin@example.com",
    "password": "admin123"
})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Login exitoso!")
    print(f"Access Token: {data['access'][:50]}...")
    access_token = data['access']
else:
    print(f"❌ Error: {response.json()}")
    exit(1)

# Test 2: Obtener info del usuario
print("\n✅ TEST 2: Información del usuario")
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/auth/me/", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    user = response.json()
    print(f"✅ Usuario: {user['first_name']} {user['last_name']}")
    print(f"   Email: {user['email']}")
    print(f"   Rol: {user['role']}")
else:
    print(f"❌ Error: {response.json()}")

print("\n✅ TODAS LAS PRUEBAS BÁSICAS COMPLETADAS")
