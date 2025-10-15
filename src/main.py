import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.attendance import Attendance
from src.models.shift import Shift
from src.models.leave_request import LeaveRequest
from src.models.qr_code import QRCode
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.attendance import attendance_bp
from src.routes.shift import shift_bp
from src.routes.leave_request import leave_request_bp
from src.routes.qr_code import qr_code_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# ============================================================================
# CONFIGURAZIONE CORS COMPLETA
# ============================================================================
# Questa configurazione permette al frontend su Vercel di comunicare con il backend su Railway
# 
# IMPORTANTE: Per la produzione, sostituisci "*" con l'URL specifico del tuo frontend Vercel
# Esempio: origins=["https://tuo-frontend.vercel.app"]
# 
# Per ora usiamo "*" per permettere qualsiasi origine durante i test

CORS(app, 
     resources={
         r"/api/*": {
             "origins": "*",  # Permetti tutte le origini (CAMBIA IN PRODUZIONE!)
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": False,  # False quando origins="*"
             "max_age": 3600  # Cache preflight per 1 ora
         }
     })

# Aggiungi headers CORS manualmente per maggiore compatibilità
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

# ============================================================================
# REGISTRAZIONE BLUEPRINT
# ============================================================================
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
app.register_blueprint(shift_bp, url_prefix='/api/shifts')
app.register_blueprint(leave_request_bp, url_prefix='/api/leave-requests')
app.register_blueprint(qr_code_bp, url_prefix='/api/qr-code')

# ============================================================================
# CONFIGURAZIONE DATABASE
# ============================================================================
# Supporta sia PostgreSQL (produzione su Railway) che SQLite (sviluppo locale)

database_url = os.environ.get('DATABASE_URL')

# Debug logging per verificare la configurazione del database
print("="*60, file=sys.stderr)
print("DATABASE CONFIGURATION", file=sys.stderr)
print("="*60, file=sys.stderr)

if database_url:
    print(f"✓ DATABASE_URL trovato", file=sys.stderr)
    print(f"  Tipo: PostgreSQL (Produzione)", file=sys.stderr)
    
    # Railway/Heroku usa postgres:// ma SQLAlchemy richiede postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print("  Convertito postgres:// -> postgresql://", file=sys.stderr)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    print("⚠ DATABASE_URL non trovato", file=sys.stderr)
    print("  Tipo: SQLite (Sviluppo locale)", file=sys.stderr)
    print("  ATTENZIONE: Questo non funzionerà su Railway!", file=sys.stderr)
    
    # Fallback a SQLite per sviluppo locale
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

print("="*60, file=sys.stderr)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Crea le tabelle del database se non esistono
with app.app_context():
    db.create_all()
    print("✓ Tabelle database create/verificate", file=sys.stderr)

# ============================================================================
# ROUTE PER SERVIRE IL FRONTEND (se presente nella cartella static)
# ============================================================================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serve i file statici del frontend se presenti.
    Questa route è utile solo se il frontend è buildato nella cartella static.
    """
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# ============================================================================
# AVVIO APPLICAZIONE
# ============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🚀 Avvio server Flask sulla porta {port}", file=sys.stderr)
    print(f"🌐 CORS abilitato per tutte le origini", file=sys.stderr)
    print(f"📡 API disponibili su /api/*\n", file=sys.stderr)
    
    app.run(host='0.0.0.0', port=port, debug=True)
