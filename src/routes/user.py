from flask import Blueprint, request, jsonify
from src.models.user import User, db
from src.routes.auth import token_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/', methods=['GET'])
@token_required
def get_users(current_user):
    try:
        # Solo admin può vedere tutti gli utenti
        if current_user.role != 'admin':
            return jsonify({'error': 'Accesso negato'}), 403
        
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    try:
        # Gli utenti possono vedere solo il proprio profilo, manager e admin possono vedere tutti
        if current_user.id != user_id and current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    try:
        # Gli utenti possono modificare solo il proprio profilo, admin può modificare tutti
        if current_user.id != user_id and current_user.role != 'admin':
            return jsonify({'error': 'Accesso negato'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        data = request.get_json()
        
        # Campi che possono essere modificati
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Verifica che l'email non sia già in uso
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Email già in uso'}), 400
            user.email = data['email']
        
        # Solo admin può modificare ruolo e stato attivo
        if current_user.role == 'admin':
            if 'role' in data:
                valid_roles = ['employee', 'manager', 'admin']
                if data['role'] in valid_roles:
                    user.role = data['role']
            if 'is_active' in data:
                user.is_active = data['is_active']
        
        # Cambio password
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Utente aggiornato con successo',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    try:
        # Solo admin può eliminare utenti
        if current_user.role != 'admin':
            return jsonify({'error': 'Accesso negato'}), 403
        
        # Non può eliminare se stesso
        if current_user.id == user_id:
            return jsonify({'error': 'Non puoi eliminare il tuo account'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Utente eliminato con successo'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        return jsonify({
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
