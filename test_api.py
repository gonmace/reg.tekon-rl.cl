#!/usr/bin/env python3
import requests
import json

# URL base
base_url = "http://localhost:8000"

# Probar la página de sitios (debería redirigir a login)
print("Probando página de sitios...")
response = requests.get(f"{base_url}/sitios/", allow_redirects=False)
print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")

# Probar la API de sitios (debería dar 401 sin autenticación)
print("\nProbando API de sitios...")
response = requests.get(f"{base_url}/api/v1/sitios/")
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Probar con credenciales (si existen)
print("\nProbando con credenciales...")
try:
    # Intentar hacer login
    login_data = {
        'username': 'admin',  # Cambiar por un usuario válido
        'password': 'admin'   # Cambiar por la contraseña correcta
    }
    
    session = requests.Session()
    response = session.post(f"{base_url}/admin/login/", data=login_data)
    print(f"Login status: {response.status_code}")
    
    if response.status_code == 200:
        # Probar la API con la sesión
        response = session.get(f"{base_url}/api/v1/sitios/")
        print(f"API con sesión status: {response.status_code}")
        print(f"API response: {response.text[:500]}")
    else:
        print("No se pudo hacer login")
        
except Exception as e:
    print(f"Error: {e}")
