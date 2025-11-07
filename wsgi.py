"""
WSGI entry point pentru Gunicorn.
Expune aplicația Flask.

IMPORTANT: Serviciile de background (Email Listener, Cleanup Service) 
sunt pornite prin gunicorn_config.py în procesul master Gunicorn.
"""

import os
import sys

# Adaugă directorul curent în path
sys.path.insert(0, os.path.dirname(__file__))

# IMPORTANT: Inițializează logging-ul ÎNAINTE de a importa alte module
from app.config import LOG_FILE
from app.logging_config import initialize_logging

logger = initialize_logging(LOG_FILE)

from app.api_server import app

# Expune aplicația pentru Gunicorn
application = app
