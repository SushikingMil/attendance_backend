#!/usr/bin/env python3
"""
Test script per le API del sistema di gestione presenze
"""

import requests
import json
from datetime import datetime, date

BASE_URL = "http://localhost:5000/api"

def test_auth_flow():
    """Test del flusso di autenticazione"""
    print("=== Test Autenticazione ===")
    
    # Test registrazione
    register_data = {
        "username": "test_user",
        "password": "password123",
        "email": "test@example.com",
        "first_name": "Mario",
        "last_name": "Rossi",
        "role": "employee"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"Registrazione: {response.status_code} - {response.json()}")
    
    # Test login
    login_data = {
        "username": "test_user",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login: {response.status_code} - {response.json()}")
    
    if response.status_code == 200:
        token = response.json()['token']
        return token
    return None

def test_attendance_flow(token):
    """Test del flusso di gestione presenze"""
    print("\n=== Test Gestione Presenze ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test punch-in
    response = requests.post(f"{BASE_URL}/attendance/punch-in", headers=headers)
    print(f"Punch-in: {response.status_code} - {response.json()}")
    
    # Test status
    response = requests.get(f"{BASE_URL}/attendance/today-status", headers=headers)
    print(f"Status oggi: {response.status_code} - {response.json()}")
    
    # Test break start
    response = requests.post(f"{BASE_URL}/attendance/break-start", headers=headers)
    print(f"Inizio pausa: {response.status_code} - {response.json()}")
    
    # Test break end
    response = requests.post(f"{BASE_URL}/attendance/break-end", headers=headers)
    print(f"Fine pausa: {response.status_code} - {response.json()}")
    
    # Test punch-out
    response = requests.post(f"{BASE_URL}/attendance/punch-out", headers=headers)
    print(f"Punch-out: {response.status_code} - {response.json()}")
    
    # Test my attendance
    response = requests.get(f"{BASE_URL}/attendance/my-attendance", headers=headers)
    print(f"Le mie presenze: {response.status_code} - {len(response.json().get('attendances', []))} record")

def test_leave_request_flow(token):
    """Test del flusso di richieste assenza"""
    print("\n=== Test Richieste Assenza ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test creazione richiesta
    leave_data = {
        "start_date": "2024-01-15",
        "end_date": "2024-01-17",
        "leave_type": "holiday",
        "reason": "Vacanze natalizie"
    }
    
    response = requests.post(f"{BASE_URL}/leave-requests/", json=leave_data, headers=headers)
    print(f"Creazione richiesta: {response.status_code} - {response.json()}")
    
    # Test visualizzazione richieste
    response = requests.get(f"{BASE_URL}/leave-requests/my-requests", headers=headers)
    print(f"Le mie richieste: {response.status_code} - {len(response.json().get('leave_requests', []))} richieste")

def test_user_profile(token):
    """Test del profilo utente"""
    print("\n=== Test Profilo Utente ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get profile
    response = requests.get(f"{BASE_URL}/users/profile", headers=headers)
    print(f"Profilo: {response.status_code} - {response.json()}")

if __name__ == "__main__":
    print("Avvio test API del sistema di gestione presenze")
    print("NOTA: Assicurati che il server Flask sia in esecuzione su localhost:5000")
    
    try:
        # Test autenticazione
        token = test_auth_flow()
        
        if token:
            # Test altre funzionalità
            test_user_profile(token)
            test_attendance_flow(token)
            test_leave_request_flow(token)
            
            print("\n=== Test completati con successo! ===")
        else:
            print("Errore nell'autenticazione, test interrotti")
            
    except requests.exceptions.ConnectionError:
        print("Errore: Impossibile connettersi al server. Assicurati che Flask sia in esecuzione.")
    except Exception as e:
        print(f"Errore durante i test: {e}")

