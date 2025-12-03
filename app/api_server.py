"""
API Server pentru integrarea cu POSnet.
Oferă endpoints pentru preluarea comenzilor și confirmarea/anularea acestora.
"""

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import json
import os
import shutil
from datetime import datetime

from app.config import (
    COMENZI_NOI, COMENZI_PROCESATE, COMENZI_ANULATE, 
    API_HOST, API_PORT, API_DEBUG, API_KEY, API_RATE_LIMIT
)
from app.logging_config import get_logger
import logging

# Obține logger-ul pentru API server
logger = get_logger("api_server")

app = Flask(__name__)

# Configurare pentru a păstra ordinea cheilor din JSON (esențial pentru POSnet)
app.json.sort_keys = False

# Configurare Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[API_RATE_LIMIT],
    storage_uri="memory://"
)


def require_api_key(f):
    """
    Decorator pentru verificarea API Key-ului.
    Verifică header-ul X-API-Key și îl compară cu valoarea din .env
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Dacă API_KEY nu este setat în .env, permite accesul (backward compatibility)
        if not API_KEY:
            logger.warning("⚠️  API_KEY nu este setat - autentificare dezactivată!")
            return f(*args, **kwargs)
        
        # Verifică header-ul
        provided_key = request.headers.get('X-API-Key')
        
        if not provided_key:
            logger.warning(f"❌ Request fără API Key de la {get_remote_address()}")
            return jsonify({
                "error": "API Key lipsește",
                "message": "Adaugă header-ul 'X-API-Key' cu cheia API validă"
            }), 401
        
        if provided_key != API_KEY:
            logger.warning(f"❌ API Key invalid de la {get_remote_address()}")
            return jsonify({
                "error": "API Key invalid",
                "message": "Cheia API furnizată este incorectă"
            }), 403
        
        # API Key valid - permite accesul
        return f(*args, **kwargs)
    
    return decorated_function


@app.route('/', methods=['GET'])
def root():
    """Root endpoint cu informații despre API."""
    return jsonify({
        "service": "eeatingh-automation",
        "version": "1.4",
        "endpoints": {
            "health": "/api/health",
            "comenzi": "/api/comenzi [GET/POST]",
            "comanda": "/api/comanda/<id_comanda>",
            "statistici": "/api/statistici",
            "webhook_test": "/api/webhook/test [POST]"
        },
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "eeatingh-automation"
    }), 200


@app.route('/api/comenzi', methods=['GET', 'POST'])
@require_api_key
def handle_comenzi():
    """
    Endpoint unificat pentru preluarea și procesarea comenzilor.
    
    GET Request:
        Return the first new unprocessed order with status "processing".
    
    POST Request:
        Process an order (confirm or cancel) OR acknowledge updates for processed orders.
    """
    if request.method == 'GET':
        # GET - Preia următoarea comandă neprocesată
        try:
            if not COMENZI_NOI.exists():
                return jsonify({
                    "message": "No new orders",
                    "status": "empty"
                }), 200
            
            # Search for the first order with status "processing". FIFO implementation added
            # 1. Colectăm doar fișierele .json
            files = [f for f in os.listdir(COMENZI_NOI) if f.endswith('.json')]
            
            # 2. Le sortăm alfabetic (implicit cronologic datorită numelui)
            files.sort()

            # 3. Iterăm prin lista curată și sortată
            for filename in files:
                filepath = COMENZI_NOI / filename
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        comanda_data = json.load(f)
                            # Verify structure and status
                        comanda_inner = comanda_data.get("comanda", {})
                        if comanda_inner.get("status_comanda") == "processing":
                                # Return the entire order object directly
                            logger.info(f"✅ Returning order #{comanda_inner.get('id_intern_comanda', 'unknown')}")
                            return jsonify(comanda_data), 200
                except Exception as e:
                    logger.error(f"Error reading file {filename}: {e}")
            
            # No orders with "processing" status found
            return jsonify({
                "message": "No new orders with 'processing' status",
                "status": "empty"
            }), 200
            
        except Exception as e:
            logger.error(f"Error fetching orders: {e}", exc_info=True)
            return jsonify({
                "error": str(e),
                "message": "Error fetching orders"
            }), 500
    
    elif request.method == 'POST':
        # POST - Procesează comanda sau primește update-uri
        try:
            # Parameter validation
            if not request.is_json:
                return jsonify({
                    "error": "Content-Type must be application/json"
                }), 400
            
            data = request.get_json()
            
            # --- CAPCANA PENTRU POS ---
            # Logăm payload-ul ca să vedem ce trimite POS-ul la "Start Livrare"
            logger.info(f"🕵️ POST RECEIVED (PAYLOAD): {json.dumps(data, ensure_ascii=False)}")
            # --------------------------

            id_comanda = data.get('id_comanda')
            operatiune = data.get('operatiune', '').upper()
            timp_livrare = data.get('timp_livrare')
            
            if not id_comanda:
                return jsonify({
                    "error": "Parameter 'id_comanda' is required"
                }), 400
            
            # --- LOGICA NOUĂ DE CĂUTARE ---
            found_path = None
            found_folder_type = None # 'noi' sau 'procesate'

            # 1. Căutăm întâi în comenzi NOI
            if COMENZI_NOI.exists():
                for filename in os.listdir(COMENZI_NOI):
                    if filename.endswith('.json') and f"comanda_{id_comanda}.json" in filename:
                        found_path = COMENZI_NOI / filename
                        found_folder_type = 'noi'
                        break
            
            # 2. Dacă nu e nouă, căutăm în PROCESATE (pentru update-uri de la POS)
            if not found_path and COMENZI_PROCESATE.exists():
                for filename in os.listdir(COMENZI_PROCESATE):
                    if filename.endswith('.json') and f"comanda_{id_comanda}.json" in filename:
                        found_path = COMENZI_PROCESATE / filename
                        found_folder_type = 'procesate'
                        break

            if not found_path:
                logger.warning(f"❌ Order #{id_comanda} not found anywhere (sending 404)")
                return jsonify({
                    "error": f"Order #{id_comanda} not found"
                }), 404
            
            # --- TRATARE ÎN FUNCȚIE DE STARE ---

            # CAZ A: Comanda este deja procesată -> Returnăm 200 OK
            if found_folder_type == 'procesate':
                logger.info(f"ℹ️ Order #{id_comanda} is already processed. Acknowledging POS update.")
                return jsonify({
                    "success": True,
                    "message": f"Order #{id_comanda} already processed. Status update received.",
                    "status": "updated"
                }), 200

            # CAZ B: Comanda este nouă -> Trebuie mutată (Confirmare/Anulare)
            if operatiune not in ['CONFIRMA', 'ANULEAZA']:
                return jsonify({
                    "error": "Parameter 'operatiune' must be 'CONFIRMA' or 'ANULEAZA'"
                }), 400
            
            # Determine destination based on operation
            if operatiune == 'CONFIRMA':
                dest_folder = COMENZI_PROCESATE
                status_message = f"Order #{id_comanda} confirmed"
                if timp_livrare:
                    status_message += f" with delivery time: {timp_livrare} minutes"
            else:
                dest_folder = COMENZI_ANULATE
                status_message = f"Order #{id_comanda} cancelled"
            
            # Create destination folder if it doesn't exist
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            # Move file
            dest_path = dest_folder / found_path.name
            shutil.move(str(found_path), str(dest_path))
            
            logger.info(status_message)
            
            return jsonify({
                "success": True,
                "message": status_message,
                "id_comanda": id_comanda,
                "operatiune": operatiune,
                "timp_livrare": timp_livrare if operatiune == 'CONFIRMA' else None,
                "moved_to": str(dest_folder.name)
            }), 200
            
        except Exception as e:
            logger.error(f"Error processing order: {e}", exc_info=True)
            return jsonify({
                "error": str(e),
                "message": "Error processing order"
            }), 500


@app.route('/api/comanda/<id_comanda>', methods=['GET'])
@require_api_key
def get_comanda(id_comanda):
    """
    Return details of a specific order.
    
    Args:
        id_comanda: Order ID to search for
    """
    try:
        # Search in all folders
        folders = [COMENZI_NOI, COMENZI_PROCESATE, COMENZI_ANULATE]
        
        for folder in folders:
            if folder.exists():
                for filename in os.listdir(folder):
                    if filename.endswith('.json') and f"comanda_{id_comanda}.json" in filename:
                        filepath = folder / filename
                        with open(filepath, 'r', encoding='utf-8') as f:
                            comanda_data = json.load(f)
                        
                        return jsonify(comanda_data), 200
        
        return jsonify({
            "error": "Order not found",
            "id_comanda": id_comanda
        }), 404
        
    except Exception as e:
        logger.error(f"Error fetching order {id_comanda}: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "message": "Error fetching order"
        }), 500



@app.route('/api/statistici', methods=['GET'])
@require_api_key
def get_statistici():
    """Return statistics about orders."""
    try:
        stats = {
            "comenzi_noi": 0,
            "comenzi_procesate": 0,
            "comenzi_anulate": 0,
            "total": 0
        }
        
        folders = {
            "comenzi_noi": COMENZI_NOI,
            "comenzi_procesate": COMENZI_PROCESATE,
            "comenzi_anulate": COMENZI_ANULATE
        }
        
        for key, folder in folders.items():
            if folder.exists():
                count = len([f for f in os.listdir(folder) if f.endswith('.json')])
                stats[key] = count
                stats["total"] += count
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "message": "Error calculating statistics"
        }), 500


@app.route('/api/webhook/test', methods=['POST'])
def webhook_test():
    """
    Endpoint de test pentru webhook-uri.
    Poate fi folosit pentru a testa integrări externe.
    """
    try:
        if not request.is_json:
            return jsonify({
                "error": "Content-Type trebuie să fie application/json"
            }), 400
        
        data = request.get_json()
        logger.info(f"📥 Webhook primit: {data}")
        
        return jsonify({
            "success": True,
            "message": "Webhook primit cu succes",
            "received_data": data,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Eroare la procesarea webhook: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "message": "Eroare la procesarea webhook"
        }), 500


@app.route('/api/webhook/notify', methods=['POST'])
def webhook_notify():
    """
    Endpoint pentru notificări externe când vine comandă nouă.
    Poate fi apelat de email_listener sau alte servicii.
    """
    try:
        if not request.is_json:
            return jsonify({
                "error": "Content-Type trebuie să fie application/json"
            }), 400
        
        data = request.get_json()
        event = data.get('event')
        order_id = data.get('order_id')
        
        logger.info(f"🔔 Notificare nouă: {event} pentru comandă #{order_id}")
        
        return jsonify({
            "success": True,
            "message": f"Notificare procesată pentru comandă #{order_id}",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Eroare la procesarea notificării: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "message": "Eroare la procesarea notificării"
        }), 500
