"""
Configurație Gunicorn pentru aplicația Eeatingh.
Pornește serviciile de background o singură dată în procesul master.
"""

import os
import sys
from threading import Thread

# Adaugă directorul curent în path
sys.path.insert(0, os.path.dirname(__file__))

# IMPORTANT: Inițializează logging-ul ÎNAINTE de a importa alte module
from app.config import LOG_FILE
from app.logging_config import initialize_logging

logger = initialize_logging(LOG_FILE)

# Variabile globale pentru servicii
email_listener = None
cleanup_service = None


def when_ready(server):
    """
    Hook Gunicorn - apelat o singură dată când serverul este gata.
    Rulează în procesul master, înainte de fork-area worker-ilor.
    """
    from app.services.email_listener import EmailListener
    from app.services.cleanup_service import CleanupService
    
    global email_listener, cleanup_service
    
    try:
        logger.info("=" * 80)
        logger.info("🚀 Pornire servicii background (Gunicorn Master Process)")
        logger.info("=" * 80)
        
        # Pornește Email Listener
        logger.info("📧 Pornire Email Listener...")
        email_listener = EmailListener()
        email_thread = Thread(target=email_listener.start, daemon=True, name="EmailListener")
        email_thread.start()
        
        # Pornește Cleanup Service
        logger.info("🧹 Pornire Cleanup Service...")
        cleanup_service = CleanupService()
        cleanup_thread = Thread(target=cleanup_service.start, daemon=True, name="CleanupService")
        cleanup_thread.start()
        
        logger.info("=" * 80)
        logger.info("✅ Servicii background pornite cu succes!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Eroare la pornirea serviciilor background: {e}", exc_info=True)


# Configurații Gunicorn
bind = "127.0.0.1:5550"
workers = 2
threads = 2
timeout = 120
worker_class = "sync"
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Preload app pentru a partaja codul între workeri (opțional, pentru performanță)
preload_app = False
