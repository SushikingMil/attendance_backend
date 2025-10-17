#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app

if __name__ == '__main__':
    # Usa la porta dalle variabili d'ambiente (Render usa PORT=10000)
    # Fallback a 5001 per sviluppo locale
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
