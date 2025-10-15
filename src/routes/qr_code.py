from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.user import db
from src.models.qr_code import QRCode
from src.models.attendance import Attendance
from src.routes.auth import token_required

qr_code_bp = Blueprint('qr_code', __name__)

@qr_code_bp.route('/generate', methods=['POST'])
@token_required
def generate_qr_code(current_user):
    """Genera un nuovo QR code unico, disattivando quello precedente"""
    try:
        # Solo admin possono generare QR code
        if current_user.role != 'admin':
            return jsonify({'error': 'Accesso negato. Solo gli admin possono generare QR code.'}), 403
        
        data = request.get_json() or {}
        description = data.get('description', 'QR Code per presenze')
        expires_hours = data.get('expires_hours', 24)  # Default: 24 ore
        
        # Disattiva tutti i QR code esistenti
        deactivated_count = QRCode.deactivate_all()
        
        # Crea il nuovo QR code
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours) if expires_hours else None
        new_qr_code = QRCode(
            created_by=current_user.id,
            description=description,
            expires_at=expires_at
        )
        
        db.session.add(new_qr_code)
        db.session.commit()
        
        return jsonify({
            'message': f'Nuovo QR code generato con successo. {deactivated_count} QR code precedenti disattivati.',
            'qr_code': new_qr_code.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/active', methods=['GET'])
@token_required
def get_active_qr_code(current_user):
    """Restituisce il QR code attivo corrente"""
    try:
        # Solo admin possono vedere il QR code attivo
        if current_user.role != 'admin':
            return jsonify({'error': 'Accesso negato'}), 403
        
        active_qr = QRCode.get_active_qr_code()
        
        if not active_qr:
            return jsonify({'message': 'Nessun QR code attivo'}), 404
        
        # Verifica se è scaduto
        if active_qr.expires_at and datetime.utcnow() > active_qr.expires_at:
            active_qr.deactivate()
            db.session.commit()
            return jsonify({'message': 'QR code scaduto e disattivato'}), 404
        
        return jsonify({
            'qr_code': active_qr.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/scan', methods=['POST'])
def scan_qr_code():
    """Endpoint per la scansione del QR code da parte dell'app mobile"""
    try:
        data = request.get_json()
        
        if not data or not data.get('token'):
            return jsonify({'error': 'Token QR code richiesto'}), 400
        
        if not data.get('user_id'):
            return jsonify({'error': 'ID utente richiesto'}), 400
        
        token = data['token']
        user_id = data['user_id']
        action = data.get('action', 'punch_in')  # punch_in, punch_out, break_in, break_out
        
        # Verifica che l'utente esista
        from src.models.user import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        # Verifica che il QR code sia valido e attivo
        qr_code = QRCode.query.filter_by(token=token, is_active=True).first()
        if not qr_code:
            return jsonify({'error': 'QR code non valido o scaduto'}), 400
        
        # Verifica se è scaduto
        if qr_code.expires_at and datetime.utcnow() > qr_code.expires_at:
            qr_code.deactivate()
            db.session.commit()
            return jsonify({'error': 'QR code scaduto'}), 400
        
        # Registra la presenza
        current_time = datetime.utcnow()
        today = current_time.date()
        
        if action == 'punch_in':
            # Verifica che non ci sia già un punch_in attivo per oggi
            existing_attendance = Attendance.query.filter_by(
                user_id=user_id,
                date=today
            ).first()
            
            if existing_attendance and existing_attendance.punch_in_time:
                return jsonify({'error': 'Hai già fatto punch-in oggi. Devi prima fare punch-out.'}), 400
            
            # Crea nuova presenza o aggiorna quella esistente
            if not existing_attendance:
                attendance = Attendance(
                    user_id=user_id,
                    date=today,
                    punch_in_time=current_time,
                    status='present'
                )
                db.session.add(attendance)
            else:
                existing_attendance.punch_in_time = current_time
                existing_attendance.status = 'present'
                attendance = existing_attendance
            
            message = 'Punch-in registrato con successo'
            
        elif action == 'punch_out':
            # Trova l'attendance di oggi
            attendance = Attendance.query.filter_by(
                user_id=user_id,
                date=today
            ).first()
            
            if not attendance or not attendance.punch_in_time:
                return jsonify({'error': 'Devi prima registrare l\'entrata'}), 400
            
            if attendance.punch_out_time:
                return jsonify({'error': 'Hai già registrato l\'uscita per oggi'}), 400
            
            attendance.punch_out_time = current_time
            attendance.status = 'absent'
            message = 'Punch-out registrato con successo'
            
        elif action == 'break_in':
            # Trova l'attendance di oggi
            attendance = Attendance.query.filter_by(
                user_id=user_id,
                date=today
            ).first()
            
            if not attendance or not attendance.punch_in_time:
                return jsonify({'error': 'Devi prima registrare l\'entrata'}), 400
            
            if attendance.break_start_time and not attendance.break_end_time:
                return jsonify({'error': 'Sei già in pausa'}), 400
            
            attendance.break_start_time = current_time
            attendance.break_end_time = None  # Reset break_end_time
            attendance.status = 'on_break'
            message = 'Inizio pausa registrato con successo'
            
        elif action == 'break_out':
            # Trova l'attendance di oggi
            attendance = Attendance.query.filter_by(
                user_id=user_id,
                date=today
            ).first()
            
            if not attendance or not attendance.break_start_time:
                return jsonify({'error': 'Non sei in pausa'}), 400
            
            if attendance.break_end_time:
                return jsonify({'error': 'Hai già terminato la pausa'}), 400
            
            attendance.break_end_time = current_time
            attendance.status = 'present'
            message = 'Fine pausa registrata con successo'
            
        else:
            return jsonify({'error': 'Azione non valida'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': message,
            'user': {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}",
                'username': user.username
            },
            'action': action,
            'timestamp': current_time.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/history', methods=['GET'])
@token_required
def get_qr_code_history(current_user):
    """Restituisce la cronologia dei QR code generati"""
    try:
        # Solo admin possono vedere la cronologia
        if current_user.role != 'admin':
            return jsonify({'error': 'Accesso negato'}), 403
        
        qr_codes = QRCode.query.order_by(QRCode.created_at.desc()).all()
        
        return jsonify({
            'qr_codes': [qr.to_dict() for qr in qr_codes]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_code_bp.route('/<int:qr_id>/deactivate', methods=['POST'])
@token_required
def deactivate_qr_code(current_user, qr_id):
    """Disattiva un QR code specifico"""
    try:
        # Solo admin possono disattivare QR code
        if current_user.role != 'admin':
            return jsonify({'error': 'Accesso negato'}), 403
        
        qr_code = QRCode.query.get(qr_id)
        if not qr_code:
            return jsonify({'error': 'QR code non trovato'}), 404
        
        if not qr_code.is_active:
            return jsonify({'error': 'QR code già disattivato'}), 400
        
        qr_code.deactivate()
        db.session.commit()
        
        return jsonify({
            'message': 'QR code disattivato con successo'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

