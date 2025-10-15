from flask import Blueprint, request, jsonify
from datetime import datetime, date
from src.models.user import db
from src.models.shift import Shift
from src.routes.auth import token_required

shift_bp = Blueprint('shift', __name__)

@shift_bp.route('/my-shifts', methods=['GET'])
@token_required
def get_my_shifts(current_user):
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Shift.query.filter_by(user_id=current_user.id)
        
        if start_date:
            query = query.filter(Shift.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Shift.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        shifts = query.order_by(Shift.date.asc()).all()
        
        return jsonify({
            'shifts': [shift.to_dict() for shift in shifts]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shift_bp.route('/', methods=['POST'])
@token_required
def create_shift(current_user):
    try:
        # Solo manager e admin possono creare turni
        if current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        data = request.get_json()
        
        required_fields = ['user_id', 'start_time', 'end_time', 'date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} è richiesto'}), 400
        
        # Verifica che l'utente esista
        from src.models.user import User
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        shift = Shift(
            user_id=data['user_id'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            description=data.get('description', '')
        )
        
        db.session.add(shift)
        db.session.commit()
        
        return jsonify({
            'message': 'Turno creato con successo',
            'shift': shift.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@shift_bp.route('/<int:shift_id>', methods=['PUT'])
@token_required
def update_shift(current_user, shift_id):
    try:
        # Solo manager e admin possono modificare turni
        if current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        shift = Shift.query.get(shift_id)
        if not shift:
            return jsonify({'error': 'Turno non trovato'}), 404
        
        data = request.get_json()
        
        if 'start_time' in data:
            shift.start_time = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data:
            shift.end_time = datetime.fromisoformat(data['end_time'])
        if 'date' in data:
            shift.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'description' in data:
            shift.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Turno aggiornato con successo',
            'shift': shift.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@shift_bp.route('/<int:shift_id>', methods=['DELETE'])
@token_required
def delete_shift(current_user, shift_id):
    try:
        # Solo manager e admin possono eliminare turni
        if current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        shift = Shift.query.get(shift_id)
        if not shift:
            return jsonify({'error': 'Turno non trovato'}), 404
        
        db.session.delete(shift)
        db.session.commit()
        
        return jsonify({
            'message': 'Turno eliminato con successo'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@shift_bp.route('/all', methods=['GET'])
@token_required
def get_all_shifts(current_user):
    try:
        # Solo manager e admin possono vedere tutti i turni
        if current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        
        query = Shift.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Shift.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Shift.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        shifts = query.order_by(Shift.date.asc()).all()
        
        return jsonify({
            'shifts': [shift.to_dict() for shift in shifts]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

