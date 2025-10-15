#!/usr/bin/env python3
"""
Script per impostare un utente come amministratore
Uso: python3 set_admin.py <username>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.models.user import db, User
from src.main import app

def set_admin(username):
    """Imposta un utente come admin"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.role = 'admin'
            db.session.commit()
            print(f"✅ Utente '{user.username}' impostato come admin")
            print(f"   Nome: {user.first_name} {user.last_name}")
            print(f"   Email: {user.email}")
            print(f"   Ruolo: {user.role}")
            return True
        else:
            print(f"❌ Utente '{username}' non trovato")
            return False

def list_users():
    """Lista tutti gli utenti"""
    with app.app_context():
        users = User.query.all()
        if users:
            print("\n📋 Utenti registrati:")
            print("-" * 60)
            for user in users:
                print(f"Username: {user.username:15} | Ruolo: {user.role:10} | Nome: {user.first_name} {user.last_name}")
            print("-" * 60)
        else:
            print("❌ Nessun utente registrato")

if __name__ == '__main__':
    print("=" * 60)
    print("  Script Gestione Admin - Sistema Gestione Presenze")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\n⚠️  Uso: python3 set_admin.py <username>")
        print("\nEsempio: python3 set_admin.py admin")
        list_users()
        sys.exit(1)
    
    username = sys.argv[1]
    success = set_admin(username)
    
    if success:
        print("\n✅ Operazione completata con successo!")
        print("   Puoi ora effettuare il login con questo utente come admin.")
    else:
        print("\n❌ Operazione fallita.")
        print("   Verifica che l'utente sia registrato.")
        list_users()
        sys.exit(1)
