from flask import Blueprint, request, jsonify
from datetime import datetime, date
from src.models.user import db
from src.models.leave_request import LeaveRequest
from src.routes.auth import token_required

leave_request_bp = Blueprint('leave_request', __name__)

@leave_request_bp.route('/', methods=['POST'])
@token_required
def create_leave_request(current_user):
    try:
        data = request.get_json()
        
        required_fields = ['start_date', 'end_date', 'leave_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} è richiesto'}), 400
        
        # Validazione tipo di assenza
        valid_leave_types = ['holiday', 'permission', 'sick_leave']
        if data['leave_type'] not in valid_leave_types:
            return jsonify({'error': 'Tipo di assenza non valido'}), 400
        
        # Validazione date
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        if start_date > end_date:
            return jsonify({'error': 'La data di inizio deve essere precedente alla data di fine'}), 400
        
        leave_request = LeaveRequest(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            leave_type=data['leave_type'],
            reason=data.get('reason', ''),
            attachment_path=data.get('attachment_path')
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        return jsonify({
            'message': 'Richiesta di assenza creata con successo',
            'leave_request': leave_request.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@leave_request_bp.route('/my-requests', methods=['GET'])
@token_required
def get_my_leave_requests(current_user):
    try:
        status = request.args.get('status')  # pending, approved, rejected
        
        query = LeaveRequest.query.filter_by(user_id=current_user.id)
        
        if status:
            query = query.filter_by(status=status)
        
        leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()
        
        return jsonify({
            'leave_requests': [lr.to_dict() for lr in leave_requests]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_request_bp.route('/<int:request_id>', methods=['PUT'])
@token_required
def update_leave_request(current_user, request_id):
    try:
        leave_request = LeaveRequest.query.get(request_id)
        if not leave_request:
            return jsonify({'error': 'Richiesta non trovata'}), 404
        
        # Solo il proprietario può modificare la richiesta se è ancora in pending
        if leave_request.user_id != current_user.id:
            return jsonify({'error': 'Accesso negato'}), 403
        
        if leave_request.status != 'pending':
            return jsonify({'error': 'Non puoi modificare una richiesta già processata'}), 400
        
        data = request.get_json()
        
        if 'start_date' in data:
            leave_request.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            leave_request.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'leave_type' in data:
            valid_leave_types = ['holiday', 'permission', 'sick_leave']
            if data['leave_type'] not in valid_leave_types:
                return jsonify({'error': 'Tipo di assenza non valido'}), 400
            leave_request.leave_type = data['leave_type']
        if 'reason' in data:
            leave_request.reason = data['reason']
        if 'attachment_path' in data:
            leave_request.attachment_path = data['attachment_path']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Richiesta aggiornata con successo',
            'leave_request': leave_request.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@leave_request_bp.route('/<int:request_id>/approve', methods=['POST'])
@token_required
def approve_leave_request(current_user, request_id):
    try:
        # Solo manager e admin possono approvare richieste
        if current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        leave_request = LeaveRequest.query.get(request_id)
        if not leave_request:
            return jsonify({'error': 'Richiesta non trovata'}), 404
        
        if leave_request.status != 'pending':
            return jsonify({'error': 'Richiesta già processata'}), 400
        
        leave_request.status = 'approved'
        leave_request.approver_id = current_user.id
        leave_request.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Richiesta approvata con successo',
            'leave_request': leave_request.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@leave_request_bp.route('/<int:request_id>/reject', methods=['POST'])
@token_required
def reject_leave_request(current_user, request_id):
    try:
        # Solo manager e admin possono rifiutare richieste
        if current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        leave_request = LeaveRequest.query.get(request_id)
        if not leave_request:
            return jsonify({'error': 'Richiesta non trovata'}), 404
        
        if leave_request.status != 'pending':
            return jsonify({'error': 'Richiesta già processata'}), 400
        
        leave_request.status = 'rejected'
        leave_request.approver_id = current_user.id
        leave_request.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Richiesta rifiutata',
            'leave_request': leave_request.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@leave_request_bp.route('/pending', methods=['GET'])
@token_required
def get_pending_requests(current_user):
    try:
        # Solo manager e admin possono vedere le richieste in sospeso
        if current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        leave_requests = LeaveRequest.query.filter_by(status='pending').order_by(LeaveRequest.created_at.asc()).all()
        
        return jsonify({
            'leave_requests': [lr.to_dict() for lr in leave_requests]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_request_bp.route('/all', methods=['GET'])
@token_required
def get_all_leave_requests(current_user):
    try:
        # Solo manager e admin possono vedere tutte le richieste
        if current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        status = request.args.get('status')
        user_id = request.args.get('user_id')
        
        query = LeaveRequest.query
        
        if status:
            query = query.filter_by(status=status)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()
        
        return jsonify({
            'leave_requests': [lr.to_dict() for lr in leave_requests]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

