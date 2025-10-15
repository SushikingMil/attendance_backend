from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
import jwt
from datetime import datetime, timedelta
from src.models.user import User, db

auth_bp = Blueprint('auth', __name__)

SECRET_KEY = 'asdf#FGSgvasgf$5$WGT'  # In produzione, usare una chiave più sicura

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username e password sono richiesti'}), 400

        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Credenziali non valide'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account disabilitato'}), 401

        # Genera JWT token
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({
            'token': token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validazione dati richiesti
        required_fields = ['username', 'password', 'email', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} è richiesto'}), 400

        # Verifica se username o email esistono già
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username già esistente'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email già esistente'}), 400

        # Crea nuovo utente
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data.get('role', 'employee')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'message': 'Utente creato con successo',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def token_required(f):
    """Decorator per verificare il token JWT"""
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token mancante'}), 401
        
        try:
            # Rimuovi "Bearer " se presente
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(payload['user_id'])
            
            if not current_user or not current_user.is_active:
                return jsonify({'error': 'Token non valido'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token scaduto'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token non valido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    decorated.__name__ = f.__name__
    return decorated

