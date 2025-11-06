"""
Configurare logging centralizată pentru aplicația Eeatingh.
"""

import logging
import sys
from pathlib import Path

# Format pentru log-uri
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Logger global (va fi inițializat prin initialize_logging)
logger = None


def initialize_logging(log_file_path: Path) -> logging.Logger:
    """
    Inițializează configurarea logging pentru întreaga aplicație.
    Această funcție trebuie apelată explicit la pornirea aplicației.
    
    Args:
        log_file_path: Calea către fișierul de log
        
    Returns:
        Logger-ul principal al aplicației
    """
    global logger
    
    # Asigură-te că directorul pentru logs există
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configurare logging de bază (force=True resetează automat handler-ele existente)
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    
    # Creează și returnează logger-ul principal
    logger = logging.getLogger("eeatingh")
    logger.setLevel(logging.INFO)
    
    # Log mesaj de confirmare
    logger.info(f"📋 Logging inițializat: {log_file_path}")
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Returnează un logger configurat.
    
    Args:
        name: Numele logger-ului (opțional)
        
    Returns:
        Logger configurat
    """
    if logger is None:
        raise RuntimeError(
            "Logging-ul nu a fost inițializat! "
            "Apelează initialize_logging() la pornirea aplicației."
        )
    
    if name:
        return logging.getLogger(f"eeatingh.{name}")
    return logger
