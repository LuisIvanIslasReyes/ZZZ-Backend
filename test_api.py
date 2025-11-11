import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 80)
print("🧪 PRUEBA DE API - Sistema de Detección de Fatiga")
print("=" * 80)

# 1. TEST: Login con superusuario
print("\n1️⃣  TEST: Login de Administrador")
print("-" * 80)
login_data = {
    "email": "admin@example.com",
    "password": "admin123"
}

try:
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        print(f"✅ Login exitoso")
        print(f"   Access Token: {access_token[:50]}...")
        print(f"   Refresh Token: {refresh_token[:50]}...")
    else:
        print(f"❌ Error en login: {response.status_code}")
        print(f"   {response.json()}")
        exit(1)
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("   ¿Está el servidor corriendo en http://localhost:8000?")
    exit(1)

# Headers con autenticación
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 2. TEST: Obtener información del usuario actual
print("\n2️⃣  TEST: Información del usuario actual")
print("-" * 80)
response = requests.get(f"{BASE_URL}/auth/me/", headers=headers)
if response.status_code == 200:
    user_data = response.json()
    print(f"✅ Usuario autenticado:")
    print(f"   Email: {user_data['email']}")
    print(f"   Nombre: {user_data['first_name']} {user_data['last_name']}")
    print(f"   Rol: {user_data['role']}")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# 3. TEST: Crear un supervisor
print("\n3️⃣  TEST: Crear Supervisor (Admin)")
print("-" * 80)
supervisor_data = {
    "email": "supervisor1@example.com",
    "password": "supervisor123",
    "password2": "supervisor123",
    "first_name": "Carlos",
    "last_name": "Supervisor",
    "role": "supervisor"
}

response = requests.post(f"{BASE_URL}/admin/supervisors/", json=supervisor_data, headers=headers)
if response.status_code == 201:
    supervisor = response.json()
    supervisor_id = supervisor['id']
    print(f"✅ Supervisor creado:")
    print(f"   ID: {supervisor['id']}")
    print(f"   Email: {supervisor['email']}")
    print(f"   Nombre: {supervisor['first_name']} {supervisor['last_name']}")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# 4. TEST: Listar supervisores
print("\n4️⃣  TEST: Listar Supervisores (Admin)")
print("-" * 80)
response = requests.get(f"{BASE_URL}/admin/supervisors/", headers=headers)
if response.status_code == 200:
    supervisors = response.json()
    print(f"✅ Total de supervisores: {len(supervisors)}")
    for sup in supervisors:
        print(f"   - {sup['first_name']} {sup['last_name']} ({sup['email']})")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# 5. TEST: Login como supervisor
print("\n5️⃣  TEST: Login de Supervisor")
print("-" * 80)
supervisor_login = {
    "email": "supervisor1@example.com",
    "password": "supervisor123"
}

response = requests.post(f"{BASE_URL}/auth/login/", json=supervisor_login)
if response.status_code == 200:
    supervisor_tokens = response.json()
    supervisor_access_token = supervisor_tokens['access']
    print(f"✅ Login de supervisor exitoso")
    print(f"   Access Token: {supervisor_access_token[:50]}...")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# Headers con token del supervisor
supervisor_headers = {
    "Authorization": f"Bearer {supervisor_access_token}",
    "Content-Type": "application/json"
}

# 6. TEST: Crear un empleado (como supervisor)
print("\n6️⃣  TEST: Crear Empleado (Supervisor)")
print("-" * 80)
employee_data = {
    "email": "employee1@example.com",
    "password": "employee123",
    "password2": "employee123",
    "first_name": "Juan",
    "last_name": "Empleado",
    "role": "employee"
}

response = requests.post(f"{BASE_URL}/supervisor/employees/", json=employee_data, headers=supervisor_headers)
if response.status_code == 201:
    employee = response.json()
    employee_id = employee['id']
    print(f"✅ Empleado creado:")
    print(f"   ID: {employee['id']}")
    print(f"   Email: {employee['email']}")
    print(f"   Nombre: {employee['first_name']} {employee['last_name']}")
    print(f"   Supervisor: {employee.get('supervisor_email', 'N/A')}")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# 7. TEST: Listar empleados (como supervisor)
print("\n7️⃣  TEST: Listar Empleados (Supervisor)")
print("-" * 80)
response = requests.get(f"{BASE_URL}/supervisor/employees/", headers=supervisor_headers)
if response.status_code == 200:
    employees = response.json()
    print(f"✅ Total de empleados bajo supervisión: {len(employees)}")
    for emp in employees:
        print(f"   - {emp['first_name']} {emp['last_name']} ({emp['email']})")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# 8. TEST: Login como empleado
print("\n8️⃣  TEST: Login de Empleado")
print("-" * 80)
employee_login = {
    "email": "employee1@example.com",
    "password": "employee123"
}

response = requests.post(f"{BASE_URL}/auth/login/", json=employee_login)
if response.status_code == 200:
    employee_tokens = response.json()
    employee_access_token = employee_tokens['access']
    print(f"✅ Login de empleado exitoso")
    print(f"   Access Token: {employee_access_token[:50]}...")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# Headers con token del empleado
employee_headers = {
    "Authorization": f"Bearer {employee_access_token}",
    "Content-Type": "application/json"
}

# 9. TEST: Obtener información del empleado
print("\n9️⃣  TEST: Información del Empleado (Me)")
print("-" * 80)
response = requests.get(f"{BASE_URL}/employee/me/", headers=employee_headers)
if response.status_code == 200:
    emp_data = response.json()
    print(f"✅ Datos del empleado:")
    print(f"   Email: {emp_data['email']}")
    print(f"   Nombre: {emp_data['first_name']} {emp_data['last_name']}")
    print(f"   Rol: {emp_data['role']}")
    print(f"   Supervisor: {emp_data.get('supervisor_email', 'N/A')}")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# 10. TEST: Refresh token
print("\n🔟 TEST: Refresh Token")
print("-" * 80)
refresh_data = {
    "refresh": refresh_token
}

response = requests.post(f"{BASE_URL}/auth/refresh/", json=refresh_data)
if response.status_code == 200:
    new_tokens = response.json()
    print(f"✅ Token refrescado exitosamente")
    print(f"   Nuevo Access Token: {new_tokens['access'][:50]}...")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# 11. TEST: Cambiar contraseña
print("\n1️⃣1️⃣  TEST: Cambiar Contraseña (Empleado)")
print("-" * 80)
change_password_data = {
    "old_password": "employee123",
    "new_password": "newpassword123",
    "new_password2": "newpassword123"
}

response = requests.post(f"{BASE_URL}/auth/change-password/", json=change_password_data, headers=employee_headers)
if response.status_code == 200:
    print(f"✅ Contraseña cambiada exitosamente")
    print(f"   {response.json()}")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# 12. TEST: Logout
print("\n1️⃣2️⃣  TEST: Logout")
print("-" * 80)
logout_data = {
    "refresh": refresh_token
}

response = requests.post(f"{BASE_URL}/auth/logout/", json=logout_data, headers=headers)
if response.status_code == 200:
    print(f"✅ Logout exitoso")
    print(f"   {response.json()}")
else:
    print(f"❌ Error: {response.status_code} - {response.json()}")

# RESUMEN
print("\n" + "=" * 80)
print("✅ TODAS LAS PRUEBAS COMPLETADAS")
print("=" * 80)
print("\n📊 RESUMEN:")
print(f"   - Superusuario Admin: admin@example.com / admin123")
print(f"   - Supervisor: supervisor1@example.com / supervisor123")
print(f"   - Empleado: employee1@example.com / newpassword123")
print("\n🔗 API Base URL: {BASE_URL}")
print("=" * 80)
