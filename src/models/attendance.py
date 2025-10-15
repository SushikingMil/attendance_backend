from datetime import datetime
from src.models.user import db

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    punch_in_time = db.Column(db.DateTime, nullable=False)
    punch_out_time = db.Column(db.DateTime, nullable=True)
    break_start_time = db.Column(db.DateTime, nullable=True)
    break_end_time = db.Column(db.DateTime, nullable=True)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='present')  # present, absent, on_break
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Attendance {self.user_id} - {self.date}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'punch_in_time': self.punch_in_time.isoformat() if self.punch_in_time else None,
            'punch_out_time': self.punch_out_time.isoformat() if self.punch_out_time else None,
            'break_start_time': self.break_start_time.isoformat() if self.break_start_time else None,
            'break_end_time': self.break_end_time.isoformat() if self.break_end_time else None,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

