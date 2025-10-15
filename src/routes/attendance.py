from flask import Blueprint, request, jsonify
from datetime import datetime, date
from src.models.user import db
from src.models.attendance import Attendance
from src.routes.auth import token_required

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/punch-in', methods=['POST'])
@token_required
def punch_in(current_user):
    try:
        today = date.today()
        
        # Verifica se esiste già una presenza per oggi
        existing_attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if existing_attendance and existing_attendance.punch_in_time:
            return jsonify({'error': 'Hai già registrato l\'entrata per oggi'}), 400
        
        # Crea nuova presenza o aggiorna quella esistente
        if not existing_attendance:
            attendance = Attendance(
                user_id=current_user.id,
                punch_in_time=datetime.utcnow(),
                date=today,
                status='present'
            )
            db.session.add(attendance)
        else:
            existing_attendance.punch_in_time = datetime.utcnow()
            existing_attendance.status = 'present'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Entrata registrata con successo',
            'attendance': existing_attendance.to_dict() if existing_attendance else attendance.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/punch-out', methods=['POST'])
@token_required
def punch_out(current_user):
    try:
        today = date.today()
        
        attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if not attendance or not attendance.punch_in_time:
            return jsonify({'error': 'Devi prima registrare l\'entrata'}), 400
        
        if attendance.punch_out_time:
            return jsonify({'error': 'Hai già registrato l\'uscita per oggi'}), 400
        
        attendance.punch_out_time = datetime.utcnow()
        attendance.status = 'absent'  # Cambia stato a absent quando esce
        
        db.session.commit()
        
        return jsonify({
            'message': 'Uscita registrata con successo',
            'attendance': attendance.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/break-start', methods=['POST'])
@token_required
def break_start(current_user):
    try:
        today = date.today()
        
        attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if not attendance or not attendance.punch_in_time:
            return jsonify({'error': 'Devi prima registrare l\'entrata'}), 400
        
        if attendance.break_start_time and not attendance.break_end_time:
            return jsonify({'error': 'Sei già in pausa'}), 400
        
        attendance.break_start_time = datetime.utcnow()
        attendance.break_end_time = None  # Reset break end time
        attendance.status = 'on_break'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Pausa iniziata',
            'attendance': attendance.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/break-end', methods=['POST'])
@token_required
def break_end(current_user):
    try:
        today = date.today()
        
        attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if not attendance or not attendance.break_start_time:
            return jsonify({'error': 'Non sei in pausa'}), 400
        
        if attendance.break_end_time:
            return jsonify({'error': 'Hai già terminato la pausa'}), 400
        
        attendance.break_end_time = datetime.utcnow()
        attendance.status = 'present'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Pausa terminata',
            'attendance': attendance.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/my-attendance', methods=['GET'])
@token_required
def get_my_attendance(current_user):
    try:
        # Parametri opzionali per filtrare per data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Attendance.query.filter_by(user_id=current_user.id)
        
        if start_date:
            query = query.filter(Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        attendances = query.order_by(Attendance.date.desc()).all()
        
        return jsonify({
            'attendances': [att.to_dict() for att in attendances]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/today-status', methods=['GET'])
@token_required
def get_today_status(current_user):
    try:
        today = date.today()
        
        attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if not attendance:
            return jsonify({
                'status': 'not_started',
                'attendance': None
            }), 200
        
        return jsonify({
            'status': attendance.status,
            'attendance': attendance.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route per manager/admin
@attendance_bp.route('/all', methods=['GET'])
@token_required
def get_all_attendance(current_user):
    try:
        # Solo manager e admin possono vedere tutte le presenze
        if current_user.role not in ['manager', 'admin']:
            return jsonify({'error': 'Accesso negato'}), 403
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        
        query = Attendance.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        attendances = query.order_by(Attendance.date.desc()).all()
        
        return jsonify({
            'attendances': [att.to_dict() for att in attendances]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

