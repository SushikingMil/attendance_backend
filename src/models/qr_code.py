from datetime import datetime
from src.models.user import db
import uuid

class QRCode(db.Model):
    __tablename__ = 'qr_code'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Relazione con l'utente che ha creato il QR code
    creator = db.relationship('User', backref='created_qr_codes')
    
    def __init__(self, created_by, description=None, expires_at=None):
        self.token = str(uuid.uuid4())
        self.created_by = created_by
        self.description = description
        self.expires_at = expires_at
        self.is_active = True
    
    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token,
            'created_by': self.created_by,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'description': self.description,
            'creator_name': f"{self.creator.first_name} {self.creator.last_name}" if self.creator else None
        }
    
    def deactivate(self):
        """Disattiva questo QR code"""
        self.is_active = False
    
    @classmethod
    def get_active_qr_code(cls):
        """Restituisce il QR code attivo corrente"""
        return cls.query.filter_by(is_active=True).first()
    
    @classmethod
    def deactivate_all(cls):
        """Disattiva tutti i QR code esistenti"""
        active_codes = cls.query.filter_by(is_active=True).all()
        for code in active_codes:
            code.deactivate()
        return len(active_codes)

