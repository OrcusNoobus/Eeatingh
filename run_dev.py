"""
Script de pornire pentru modul DEZVOLTARE.
Pornește aplicația cu Flask development server și logging activ.

Utilizare:
    python run_dev.py
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

from app.api_server import app
from app.services.email_listener import EmailListener
from app.services.cleanup_service import CleanupService

# Instanțe globale
email_listener = None
cleanup_service = None


def start_background_services():
    """Pornește serviciile în background (Email Listener și Cleanup Service)."""
    global email_listener, cleanup_service
    
    try:
        logger.info("=" * 80)
        logger.info("🚀 Pornire servicii background (MOD DEZVOLTARE)")
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


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🔧 MODUL DEZVOLTARE - Pornire Flask Development Server")
    logger.info("=" * 80)
    logger.info("⚠️  Acest mod este DOAR pentru dezvoltare/testare locală")
    logger.info("⚠️  În producție folosește Docker cu Gunicorn")
    logger.info("=" * 80)
    
    # Pornește serviciile în background
    start_background_services()
    
    # Pornește serverul Flask de dezvoltare
    # Acest server va menține aplicația activă și va permite
    # serviciilor background (Email Listener, Cleanup) să ruleze continuu
    logger.info("🌐 Pornire API Server pe http://0.0.0.0:5550")
    logger.info("=" * 80)
    
    app.run(
        host='0.0.0.0',
        port=5550,
        debug=False,  # Debug=False pentru a evita restart-uri automate
        use_reloader=False  # Dezactivează reloader-ul pentru a evita pornirea dublă a serviciilor
    )
