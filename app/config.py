"""
Configurație centralizată pentru aplicația Eeatingh.
Toate setările, constantele și căile sunt definite aici.
"""

import os
from pathlib import Path
from typing import Optional
import dotenv

# Încarcă variabilele de mediu din .env
dotenv.load_dotenv()

# Directoare de bază
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"

# Directoare pentru comenzi
COMENZI_DIR = BASE_DIR / "comenzi"
COMENZI_NOI = COMENZI_DIR / "noi"
COMENZI_PROCESATE = COMENZI_DIR / "procesate"
COMENZI_ANULATE = COMENZI_DIR / "anulate"

# Directoare pentru logs
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "app.log"

# Fișiere
ORDER_COUNTER_FILE = LOGS_DIR / "order_counter.txt"

# Credențiale Email din .env
EMAIL_USER: Optional[str] = os.getenv("EMAIL_USER")
EMAIL_PASS: Optional[str] = os.getenv("EMAIL_PASS")
NOTIFICATION_RECIPIENT: Optional[str] = os.getenv("NOTIFICATION_RECIPIENT")

# Validare credențiale
if not EMAIL_USER or not EMAIL_PASS:
    raise ValueError("EMAIL_USER și EMAIL_PASS trebuie definite în fișierul .env")

# Configurări Email
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Configurări Email Listener
IDLE_TIMEOUT = 20 * 60  # 20 minute
EMAIL_SENDER = "royalmures@gmail.com"  # Expeditorul așteptat pentru comenzi

# Configurări Cleanup
CLEANUP_THRESHOLD = 15  # Rulează cleanup la fiecare 15 comenzi
CLEANUP_DAYS_OLD = 3    # Șterge emailuri mai vechi de 3 zile
CLEANUP_FILES_DAYS_OLD = 7  # Șterge fișiere comenzi mai vechi de 7 zile
CLEANUP_FILES_INTERVAL = 24 * 60 * 60  # Interval de curățare fișiere (24 ore în secunde)

# Configurări API Server
API_HOST = "0.0.0.0"
API_PORT = 5550
API_DEBUG = False

# Securitate API
API_KEY: Optional[str] = os.getenv("API_KEY")  # Cheie API pentru autentificare
API_RATE_LIMIT = "100/minute"  # Limită de request-uri per minut

# Gunicorn (pentru producție)
GUNICORN_WORKERS = 2  # Număr de worker-i (pentru trafic redus)
GUNICORN_THREADS = 2  # Thread-uri per worker
GUNICORN_TIMEOUT = 120  # Timeout în secunde

# Timezone
TIMEZONE = "Europe/Bucharest"


def create_directories():
    """Creează toate directoarele necesare dacă nu există."""
    directories = [
        COMENZI_NOI,
        COMENZI_PROCESATE,
        COMENZI_ANULATE,
        LOGS_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Creează directoarele la import
create_directories()
