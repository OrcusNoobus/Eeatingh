# 🏗️ System Architecture | Arhitectura Sistemului

**Eeatingh Order Automation System v1.4**

---

## 🇺🇸 English Documentation

### Overview

The Eeatingh Order Automation System is a production-ready application designed to automatically process food delivery orders received via email. The system uses a microservices-inspired architecture with clear separation of concerns, running as a single containerized application.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Container                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐         ┌──────────────────┐                │
│  │  Email Service │         │   API Service    │                │
│  │  (IMAP IDLE)   │◄────────┤  (Flask/Gunicorn)│                │
│  └────────┬───────┘         └────────┬─────────┘                │
│           │                          │                           │
│           │    ┌─────────────────────┤                           │
│           │    │                     │                           │
│           ▼    ▼                     ▼                           │
│  ┌─────────────────────────────────────────┐                    │
│  │      Order Processing Service           │                    │
│  │  • HTML Parser (BeautifulSoup)          │                    │
│  │  • Intelligent Content Detection        │                    │
│  │  • JSON Serialization                   │                    │
│  └─────────────────┬───────────────────────┘                    │
│                    │                                             │
│                    ▼                                             │
│  ┌─────────────────────────────────────────┐                    │
│  │         File System Storage             │                    │
│  │  comenzi/noi/       - New orders        │                    │
│  │  comenzi/procesate/ - Confirmed orders  │                    │
│  │  comenzi/anulate/   - Cancelled orders  │                    │
│  │  logs/app.log       - Application logs  │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                   │
│  ┌─────────────────────────────────────────┐                    │
│  │      Cleanup Service (Automatic)        │                    │
│  │  • Email Cleanup (30+ days old)         │                    │
│  │  • JSON File Cleanup (automatic)        │                    │
│  │  • Counter-based Triggers               │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                   │
│  ┌─────────────────────────────────────────┐                    │
│  │      Notification Service               │                    │
│  │  • Error Notifications via Email        │                    │
│  │  • Critical System Alerts               │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                           ▲                  │
                           │                  │
                 ┌─────────┴────────┐  ┌──────▼──────┐
                 │  Gmail IMAP      │  │   External  │
                 │  (eeatingh.ro)   │  │   POS API   │
                 └──────────────────┘  └─────────────┘
```

### Component Breakdown

#### 1. Email Listener Service (`email_listener.py`)

**Purpose**: Real-time monitoring of incoming orders via IMAP IDLE protocol.

**Key Features**:
- **IMAP IDLE**: Push notifications for instant order processing (1-3 seconds)
- **Connection Management**: Auto-reconnect on timeout/failure
- **Unread Email Processing**: Processes backlog on startup
- **Integrated Cleanup**: Automatic old email deletion after N orders

**Technical Details**:
```python
class EmailListener:
    - connect() -> bool              # Establish IMAP connection
    - disconnect()                   # Clean disconnect
    - idle_loop()                    # Main IDLE monitoring loop
    - process_new_email(id) -> bool  # Process single email
    - cleanup_old_emails(days)       # Delete old emails
    - increment_order_counter()      # Track processed orders
```

**Flow**:
1. Connect to Gmail IMAP server (SSL)
2. Enter IDLE mode (low-power listening)
3. On notification: Exit IDLE → Process email → Re-enter IDLE
4. Every 29 minutes: Reconnect (IMAP timeout prevention)
5. Every 100 orders: Trigger cleanup service

#### 2. Order Service (`order_service.py`)

**Purpose**: Intelligent HTML parsing and order data extraction.

**Key Innovation - Content-Based Detection** (v1.4):

Instead of relying on fixed positions, the parser analyzes content:

```python
# Phone Detection
phone_pattern = r'^(\+?4?0?7\d{8}|\d{10}|\+?\d{11,12})$'

# Address Detection
- Google Maps link presence
- Address keywords: str, bloc, judet, principala, etc. (with word boundaries)
- Pattern: numbers + commas

# Name Detection
- Remaining text after phone/address extraction
- Filters: 1-5 words, no digits, no commas
```

**Functions**:
```python
parse_order_html(html) -> Dict      # Main parser
save_order_json(data, folder)       # Save to JSON
is_order_processed(order_id) -> bool # Duplicate check
parse_romanian_date(date_str) -> str # Date normalization
remove_diacritics(text) -> str      # Romanian character handling
```

**Data Flow**:
```
Raw HTML Email
    ↓
BeautifulSoup Parsing
    ↓
Content Analysis (regex patterns)
    ↓
Field Extraction
    ├── Order ID (required)
    ├── Client Data (name, phone, address)
    ├── Payment Method (CASH/CARD/ONLINE)
    ├── Products List
    ├── Total Value
    └── Order Date
    ↓
JSON Serialization
    ↓
File System Storage
```

#### 3. API Server (`api_server.py`)

**Purpose**: REST API for external POS system integration.

**Endpoints**:

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/health` | GET | None | Health check |
| `/api/comenzi` | GET | API Key | Get next unprocessed order |
| `/api/comenzi` | POST | API Key | Confirm/Cancel order |
| `/api/comanda/<id>` | GET | API Key | Get specific order details |
| `/api/statistici` | GET | API Key | Order statistics |

**Security Features**:
- API Key authentication (X-API-Key header)
- Rate limiting (100 req/min per IP)
- Request validation
- Structured logging (Fail2Ban ready)

**Technology Stack**:
- **Flask**: Web framework
- **Gunicorn**: WSGI production server (4 workers)
- **Flask-Limiter**: Rate limiting middleware

#### 4. Cleanup Service (`cleanup_service.py`)

**Purpose**: Automatic maintenance and storage optimization.

**Features**:
- **Email Cleanup**: Delete emails older than 30 days from Gmail
- **JSON Cleanup**: Remove old order files based on retention policy
- **Counter-Based Triggers**: Run after every 100 processed orders
- **Manual Triggers**: Can be invoked via API endpoint

**Configuration** (in `config.py`):
```python
CLEANUP_THRESHOLD = 100      # Orders before cleanup
CLEANUP_DAYS_OLD = 30        # Email age threshold
JSON_RETENTION_DAYS = 90     # JSON file retention
```

#### 5. Notification Service (`notification_service.py`)

**Purpose**: Error alerting and system monitoring.

**Capabilities**:
- Send email notifications on critical errors
- Formatting for easy reading
- Context-aware error messages
- Integration with email_listener and order_service

**Usage**:
```python
NotificationService().send_error_notification(
    error_message=str(exception),
    context="EmailListener - idle_loop"
)
```

### Data Models

#### Order JSON Structure

```json
{
  "comanda": {
    "id_intern_comanda": "6492",
    "simbol_monetar": "RON",
    "email_client": "",
    "numar_telefon_client": "+40749900372",
    "nume_client": "Pap Gyozo",
    "cartier": "",
    "tip_comanda": "livrare",
    "adresa_livrare_client": "Principala 429, Ceuasu de Campie",
    "valoare_comanda": "53.00",
    "discounturi": [],
    "status_comanda": "processing",
    "mod_plata": "CASH",
    "observatii_comanda": "",
    "data_comanda": "2025-10-24 19:06:00",
    "produse_comanda": [
      {
        "id_produs": null,
        "denumire_produs": "Chicken - Medie (Pizza)",
        "cantitate_produs": 1,
        "pret_produs": "49.00",
        "id_intern_comanda": "6492",
        "observatii_produs": "",
        "extra": []
      }
    ]
  }
}
```

### Configuration Management

**Environment Variables** (`.env`):
```env
# Email Configuration
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=app-specific-password
NOTIFICATION_RECIPIENT=admin@example.com

# Email Source
EMAIL_SENDER=noreply@eeatingh.ro

# API Security
API_KEY=your-secret-api-key

# Cleanup Configuration
CLEANUP_THRESHOLD=100
CLEANUP_DAYS_OLD=30
```

**Config File** (`config.py`):
- Centralizes all configuration
- Path definitions (COMENZI_NOI, COMENZI_PROCESATE, etc.)
- Email server settings (IMAP_SERVER, IMAP_PORT)
- Timeout configurations (IDLE_TIMEOUT)

### Deployment Architecture

#### Docker Setup

**Single Container Approach**:
- **Base Image**: Python 3.11-slim
- **Process Management**: Single entrypoint (wsgi.py)
- **Port Exposure**: 5000 (API server)
- **Volume Mounts**:
  - `./comenzi` → Order storage
  - `./logs` → Application logs

**docker-compose.yml**:
```yaml
services:
  eeatingh:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./comenzi:/app/comenzi
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
```

#### Process Architecture (Inside Container)

```
wsgi.py (Main Entry Point)
    │
    ├─► Thread 1: Email Listener (IMAP IDLE)
    │   └─► Continuously monitors Gmail
    │
    └─► Thread 2: API Server (Gunicorn)
        └─► 4 Worker Processes
            └─► Handle HTTP requests
```

### Design Patterns

#### 1. Service Layer Pattern
Each service is isolated with clear responsibilities:
- `EmailListener`: Email monitoring
- `OrderService`: Business logic
- `CleanupService`: Maintenance
- `NotificationService`: Alerting

#### 2. Repository Pattern
File system acts as data repository with abstraction:
```python
save_order_json(order_data, folder)
is_order_processed(order_id)
```

#### 3. Facade Pattern
`wsgi.py` provides single entry point hiding complexity:
```python
# Single command starts everything
python wsgi.py
```

#### 4. Observer Pattern (IMAP IDLE)
Email Listener waits for notifications from IMAP server:
```python
mail.idle()
responses = mail.idle_check(timeout=30)
```

### Error Handling Strategy

#### 1. Graceful Degradation
- Email connection fails → Retry every 30 seconds
- Parsing fails → Log error, send notification, continue
- API errors → Return structured JSON error

#### 2. Error Notification
Critical errors trigger email alerts:
```python
try:
    # Critical operation
except Exception as e:
    NotificationService().send_error_notification(
        error_message=str(e),
        context="Operation context"
    )
```

#### 3. Centralized Logging
All logs go to `logs/app.log`:
```python
logger = get_logger("service_name")
logger.info("✅ Success message")
logger.error("❌ Error message", exc_info=True)
```

### Performance Characteristics

#### Response Times
- **Email Detection**: 1-3 seconds (IMAP IDLE push)
- **Order Parsing**: < 100ms per order
- **API Response**: < 50ms (local file read)
- **Cleanup Operation**: 2-5 seconds per 100 emails

#### Scalability Considerations
- **Throughput**: ~1000 orders/hour (limited by Gmail IMAP)
- **Storage**: ~5KB per order JSON
- **Memory**: ~100MB baseline (Python + libraries)
- **CPU**: Low usage (event-driven architecture)

#### Bottlenecks
1. **Gmail IMAP Rate Limits**: Max ~1 request/second
2. **File System I/O**: Negligible for current volume
3. **Gunicorn Workers**: 4 workers handle concurrent API requests

### Security Architecture

#### 1. Authentication
- **API Key**: Shared secret (X-API-Key header)
- **Gmail**: App-specific password (not account password)

#### 2. Rate Limiting
```python
@limiter.limit("100 per minute")
def api_endpoint():
    pass
```

#### 3. Input Validation
- HTML sanitization via BeautifulSoup
- JSON schema validation
- Regex pattern matching (prevents injection)

#### 4. Docker Isolation
- Containerized environment
- No direct host access
- Volume mounts for data only

### Logging Architecture

#### Log Levels
- **INFO**: Normal operations (✅ success icons)
- **WARNING**: Recoverable issues (⚠️ warning icons)
- **ERROR**: Failures requiring attention (❌ error icons)

#### Log Format
```
2025-11-26 10:30:45 - order_service - INFO - ✅ Order #6492 saved
2025-11-26 10:31:02 - email_listener - ERROR - ❌ IMAP connection failed
```

#### Log Rotation
Handled by Docker/host system (recommended):
```bash
# logrotate config
/app/logs/app.log {
    daily
    rotate 30
    compress
    missingok
}
```

### Monitoring & Observability

#### Health Checks
```bash
# Container health
docker-compose ps

# API health
curl http://localhost:5000/api/health

# Logs
docker-compose logs -f
tail -f logs/app.log
```

#### Key Metrics to Monitor
- Email processing rate
- API response times
- Error rates (grep "ERROR" logs/app.log)
- Disk usage (comenzi/ folder)
- IMAP connection stability

### Testing Strategy

#### Unit Testing (Recommended)
```python
# test_order_service.py
def test_parse_order_without_name():
    html = load_fixture("order_6615.html")
    result = parse_order_html(html)
    assert result["comanda"]["nume_client"] is None
    assert result["comanda"]["numar_telefon_client"] == "0755828064"
```

#### Integration Testing
```bash
# Test email processing
python -m app.services.email_listener

# Test API
curl -H "X-API-Key: test-key" http://localhost:5000/api/comenzi
```

#### Production Testing
Real orders from eeatingh.ro platform (orders #6615, #6492, #6618 validated in v1.4)

### Future Enhancements

#### Potential Improvements
1. **Database Integration**: Replace file system with PostgreSQL/MongoDB
2. **Message Queue**: Add RabbitMQ/Redis for async processing
3. **Web Dashboard**: Real-time order monitoring UI
4. **Metrics**: Prometheus + Grafana for observability
5. **Multi-tenant**: Support multiple restaurants
6. **Webhooks**: Real-time POS notifications
7. **Order Status Tracking**: Delivery progress updates

#### Scalability Path
```
Current: Single Docker Container
    ↓
Phase 1: Database + Redis Cache
    ↓
Phase 2: Separate Services (microservices)
    ├── Email Service (dedicated container)
    ├── API Service (load balanced)
    ├── Cleanup Service (cron job)
    └── Database (PostgreSQL cluster)
    ↓
Phase 3: Kubernetes Deployment
    └── Auto-scaling, High Availability
```

---

## 🇷🇴 Documentație în Limba Română

### Prezentare Generală

Sistemul de Automatizare Comenzi Eeatingh este o aplicație production-ready concepută pentru a procesa automat comenzi de livrare primite prin email. Sistemul folosește o arhitectură inspirată din microservicii cu separare clară a responsabilităților, rulând ca o singură aplicație containerizată.

### Arhitectură la Nivel Înalt

```
┌─────────────────────────────────────────────────────────────────┐
│                      Container Docker                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐         ┌──────────────────┐                │
│  │  Serviciu Email│         │   Serviciu API   │                │
│  │  (IMAP IDLE)   │◄────────┤  (Flask/Gunicorn)│                │
│  └────────┬───────┘         └────────┬─────────┘                │
│           │                          │                           │
│           │    ┌─────────────────────┤                           │
│           │    │                     │                           │
│           ▼    ▼                     ▼                           │
│  ┌─────────────────────────────────────────┐                    │
│  │   Serviciu Procesare Comenzi            │                    │
│  │  • Parser HTML (BeautifulSoup)          │                    │
│  │  • Detectare Inteligentă Conținut       │                    │
│  │  • Serializare JSON                     │                    │
│  └─────────────────┬───────────────────────┘                    │
│                    │                                             │
│                    ▼                                             │
│  ┌─────────────────────────────────────────┐                    │
│  │      Stocare Sistem de Fișiere          │                    │
│  │  comenzi/noi/       - Comenzi noi       │                    │
│  │  comenzi/procesate/ - Comenzi confirmate│                    │
│  │  comenzi/anulate/   - Comenzi anulate   │                    │
│  │  logs/app.log       - Log-uri aplicație │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                   │
│  ┌─────────────────────────────────────────┐                    │
│  │    Serviciu Curățare (Automat)          │                    │
│  │  • Curățare Emailuri (30+ zile)         │                    │
│  │  • Curățare Fișiere JSON (automat)      │                    │
│  │  • Declanșare pe Bază de Contor         │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                   │
│  ┌─────────────────────────────────────────┐                    │
│  │      Serviciu Notificări                │                    │
│  │  • Notificări Erori prin Email          │                    │
│  │  • Alerte Critice de Sistem             │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                           ▲                  │
                           │                  │
                 ┌─────────┴────────┐  ┌──────▼──────┐
                 │  Gmail IMAP      │  │   API POS   │
                 │  (eeatingh.ro)   │  │   Extern    │
                 └──────────────────┘  └─────────────┘
```

### Detalii Componente

#### 1. Serviciu Ascultare Email (`email_listener.py`)

**Scop**: Monitorizare în timp real a comenzilor primite prin protocolul IMAP IDLE.

**Caracteristici Cheie**:
- **IMAP IDLE**: Notificări push pentru procesare instantanee (1-3 secunde)
- **Gestionare Conexiuni**: Reconectare automată la timeout/eroare
- **Procesare Emailuri Necitite**: Procesează backlog-ul la pornire
- **Curățare Integrată**: Ștergere automată emailuri vechi după N comenzi

**Detalii Tehnice**:
```python
class EmailListener:
    - connect() -> bool              # Stabilește conexiune IMAP
    - disconnect()                   # Deconectare curată
    - idle_loop()                    # Loop principal monitorizare IDLE
    - process_new_email(id) -> bool  # Procesează un singur email
    - cleanup_old_emails(days)       # Șterge emailuri vechi
    - increment_order_counter()      # Urmărește comenzi procesate
```

**Flux**:
1. Conectare la server Gmail IMAP (SSL)
2. Intrare în modul IDLE (ascultare low-power)
3. La notificare: Ieșire din IDLE → Procesare email → Reintrare IDLE
4. La fiecare 29 minute: Reconectare (prevenire timeout IMAP)
5. La fiecare 100 comenzi: Declanșare serviciu curățare

#### 2. Serviciu Comenzi (`order_service.py`)

**Scop**: Parsare inteligentă HTML și extragere date comandă.

**Inovație Cheie - Detectare pe Bază de Conținut** (v1.4):

În loc să se bazeze pe poziții fixe, parser-ul analizează conținutul:

```python
# Detectare Telefon
phone_pattern = r'^(\+?4?0?7\d{8}|\d{10}|\+?\d{11,12})$'

# Detectare Adresă
- Prezență link Google Maps
- Cuvinte cheie adresă: str, bloc, judet, principala, etc. (cu word boundaries)
- Pattern: numere + virgule

# Detectare Nume
- Text rămas după extragere telefon/adresă
- Filtre: 1-5 cuvinte, fără cifre, fără virgule
```

**Funcții**:
```python
parse_order_html(html) -> Dict      # Parser principal
save_order_json(data, folder)       # Salvare în JSON
is_order_processed(order_id) -> bool # Verificare duplicate
parse_romanian_date(date_str) -> str # Normalizare dată
remove_diacritics(text) -> str      # Gestionare caractere românești
```

**Flux de Date**:
```
Email HTML Brut
    ↓
Parsare BeautifulSoup
    ↓
Analiză Conținut (pattern-uri regex)
    ↓
Extragere Câmpuri
    ├── ID Comandă (obligatoriu)
    ├── Date Client (nume, telefon, adresă)
    ├── Mod Plată (CASH/CARD/ONLINE)
    ├── Listă Produse
    ├── Valoare Totală
    └── Dată Comandă
    ↓
Serializare JSON
    ↓
Stocare Sistem Fișiere
```

#### 3. Server API (`api_server.py`)

**Scop**: API REST pentru integrare cu sistemul POS extern.

**Endpoints**:

| Endpoint | Metodă | Auth | Scop |
|----------|--------|------|------|
| `/api/health` | GET | Fără | Health check |
| `/api/comenzi` | GET | API Key | Obține următoarea comandă neprocesată |
| `/api/comenzi` | POST | API Key | Confirmă/Anulează comandă |
| `/api/comanda/<id>` | GET | API Key | Detalii comandă specifică |
| `/api/statistici` | GET | API Key | Statistici comenzi |

**Caracteristici Securitate**:
- Autentificare API Key (header X-API-Key)
- Rate limiting (100 req/min per IP)
- Validare request-uri
- Logging structurat (Fail2Ban ready)

**Stack Tehnologic**:
- **Flask**: Framework web
- **Gunicorn**: Server WSGI producție (4 workers)
- **Flask-Limiter**: Middleware rate limiting

#### 4. Serviciu Curățare (`cleanup_service.py`)

**Scop**: Întreținere automată și optimizare stocare.

**Caracteristici**:
- **Curățare Emailuri**: Șterge emailuri mai vechi de 30 zile din Gmail
- **Curățare JSON**: Elimină fișiere comenzi vechi conform politicii de retenție
- **Declanșare pe Contor**: Rulează după fiecare 100 comenzi procesate
- **Declanșare Manuală**: Poate fi invocat prin endpoint API

**Configurare** (în `config.py`):
```python
CLEANUP_THRESHOLD = 100      # Comenzi înainte de curățare
CLEANUP_DAYS_OLD = 30        # Prag vârstă emailuri
JSON_RETENTION_DAYS = 90     # Retenție fișiere JSON
```

#### 5. Serviciu Notificări (`notification_service.py`)

**Scop**: Alertare erori și monitorizare sistem.

**Capabilități**:
- Trimite notificări email la erori critice
- Formatare pentru citire ușoară
- Mesaje eroare context-aware
- Integrare cu email_listener și order_service

**Utilizare**:
```python
NotificationService().send_error_notification(
    error_message=str(exception),
    context="EmailListener - idle_loop"
)
```

### Modele de Date

#### Structură JSON Comandă

```json
{
  "comanda": {
    "id_intern_comanda": "6492",
    "simbol_monetar": "RON",
    "email_client": "",
    "numar_telefon_client": "+40749900372",
    "nume_client": "Pap Gyozo",
    "cartier": "",
    "tip_comanda": "livrare",
    "adresa_livrare_client": "Principala 429, Ceuasu de Campie",
    "valoare_comanda": "53.00",
    "discounturi": [],
    "status_comanda": "processing",
    "mod_plata": "CASH",
    "observatii_comanda": "",
    "data_comanda": "2025-10-24 19:06:00",
    "produse_comanda": [
      {
        "id_produs": null,
        "denumire_produs": "Chicken - Medie (Pizza)",
        "cantitate_produs": 1,
        "pret_produs": "49.00",
        "id_intern_comanda": "6492",
        "observatii_produs": "",
        "extra": []
      }
    ]
  }
}
```

### Gestionare Configurație

**Variabile de Mediu** (`.env`):
```env
# Configurare Email
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=app-specific-password
NOTIFICATION_RECIPIENT=admin@example.com

# Sursă Email
EMAIL_SENDER=noreply@eeatingh.ro

# Securitate API
API_KEY=your-secret-api-key

# Configurare Curățare
CLEANUP_THRESHOLD=100
CLEANUP_DAYS_OLD=30
```

**Fișier Config** (`config.py`):
- Centralizează toată configurația
- Definiții căi (COMENZI_NOI, COMENZI_PROCESATE, etc.)
- Setări server email (IMAP_SERVER, IMAP_PORT)
- Configurații timeout (IDLE_TIMEOUT)

### Arhitectură Deployment

#### Setup Docker

**Abordare Container Unic**:
- **Imagine Bază**: Python 3.11-slim
- **Gestionare Procese**: Entrypoint unic (wsgi.py)
- **Expunere Port**: 5000 (server API)
- **Montări Volume**:
  - `./comenzi` → Stocare comenzi
  - `./logs` → Log-uri aplicație

**docker-compose.yml**:
```yaml
services:
  eeatingh:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./comenzi:/app/comenzi
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
```

#### Arhitectură Procese (În Container)

```
wsgi.py (Punct de Intrare Principal)
    │
    ├─► Thread 1: Email Listener (IMAP IDLE)
    │   └─► Monitorizează continuu Gmail
    │
    └─► Thread 2: Server API (Gunicorn)
        └─► 4 Procese Worker
            └─► Gestionează request-uri HTTP
```

### Pattern-uri de Design

#### 1. Service Layer Pattern
Fiecare serviciu este izolat cu responsabilități clare:
- `EmailListener`: Monitorizare email
- `OrderService`: Logică business
- `CleanupService`: Întreținere
- `NotificationService`: Alertare

#### 2. Repository Pattern
Sistemul de fișiere acționează ca repository de date cu abstractizare:
```python
save_order_json(order_data, folder)
is_order_processed(order_id)
```

#### 3. Facade Pattern
`wsgi.py` oferă un punct unic de intrare ascunzând complexitatea:
```python
# O singură comandă pornește totul
python wsgi.py
```

#### 4. Observer Pattern (IMAP IDLE)
Email Listener așteaptă notificări de la serverul IMAP:
```python
mail.idle()
responses = mail.idle_check(timeout=30)
```

### Strategie Gestionare Erori

#### 1. Degradare Grațioasă
- Conexiune email eșuează → Reîncearcă la fiecare 30 secunde
- Parsare eșuează → Loghează eroare, trimite notificare, continuă
- Erori API → Returnează eroare JSON structurată

#### 2. Notificare Erori
Erorile critice declanșează alerte email:
```python
try:
    # Operație critică
except Exception as e:
    NotificationService().send_error_notification(
        error_message=str(e),
        context="Context operație"
    )
```

#### 3. Logging Centralizat
Toate log-urile merg în `logs/app.log`:
```python
logger = get_logger("service_name")
logger.info("✅ Mesaj succes")
logger.error("❌ Mesaj eroare", exc_info=True)
```

### Caracteristici Performanță

#### Timpi de Răspuns
- **Detectare Email**: 1-3 secunde (IMAP IDLE push)
- **Parsare Comandă**: < 100ms per comandă
- **Răspuns API**: < 50ms (citire fișier local)
- **Operație Curățare**: 2-5 secunde per 100 emailuri

#### Considerații Scalabilitate
- **Throughput**: ~1000 comenzi/oră (limitat de Gmail IMAP)
- **Stocare**: ~5KB per JSON comandă
- **Memorie**: ~100MB baseline (Python + biblioteci)
- **CPU**: Utilizare scăzută (arhitectură event-driven)

#### Bottleneck-uri
1. **Rate Limits Gmail IMAP**: Max ~1 request/secundă
2. **I/O Sistem Fișiere**: Neglijabil pentru volum curent
3. **Workers Gunicorn**: 4 workers gestionează request-uri API concurente

### Arhitectură Securitate

#### 1. Autentificare
- **API Key**: Secret partajat (header X-API-Key)
- **Gmail**: Parolă specifică aplicație (nu parola contului)

#### 2. Rate Limiting
```python
@limiter.limit("100 per minute")
def api_endpoint():
    pass
```

#### 3. Validare Input
- Sanitizare HTML prin BeautifulSoup
- Validare schemă JSON
- Pattern matching regex (previne injection)

#### 4. Izolare Docker
- Environment containerizat
- Fără acces direct host
- Montări volume doar pentru date

### Arhitectură Logging

#### Nivele Log
- **INFO**: Operații normale (✅ icoane succes)
- **WARNING**: Probleme recuperabile (⚠️ icoane warning)
- **ERROR**: Eșecuri ce necesită atenție (❌ icoane eroare)

#### Format Log
```
2025-11-26 10:30:45 - order_service - INFO - ✅ Order #6492 saved
2025-11-26 10:31:02 - email_listener - ERROR - ❌ IMAP connection failed
```

#### Rotație Log
Gestionată de Docker/sistem host (recomandat):
```bash
# config logrotate
/app/logs/app.log {
    daily
    rotate 30
    compress
    missingok
}
```

### Monitorizare & Observabilitate

#### Health Checks
```bash
# Health container
docker-compose ps

# Health API
curl http://localhost:5000/api/health

# Log-uri
docker-compose logs -f
tail -f logs/app.log
```

#### Metrici Cheie de Monitorizat
- Rată procesare emailuri
- Timpi răspuns API
- Rate erori (grep "ERROR" logs/app.log)
- Utilizare disc (folder comenzi/)
- Stabilitate conexiune IMAP

### Strategie Testare

#### Testare Unit (Recomandat)
```python
# test_order_service.py
def test_parse_order_without_name():
    html = load_fixture("order_6615.html")
    result = parse_order_html(html)
    assert result["comanda"]["nume_client"] is None
    assert result["comanda"]["numar_telefon_client"] == "0755828064"
```

#### Testare Integrare
```bash
# Test procesare email
python -m app.services.email_listener

# Test API
curl -H "X-API-Key: test-key" http://localhost:5000/api/comenzi
```

#### Testare Producție
Comenzi reale de pe platforma eeatingh.ro (comenzi #6615, #6492, #6618 validate în v1.4)

### Îmbunătățiri Viitoare

#### Îmbunătățiri Potențiale
1. **Integrare Bază de Date**: Înlocuire sistem fișiere cu PostgreSQL/MongoDB
2. **Message Queue**: Adăugare RabbitMQ/Redis pentru procesare async
3. **Dashboard Web**: UI monitorizare comenzi în timp real
4. **Metrici**: Prometheus + Grafana pentru observabilitate
5. **Multi-tenant**: Suport restaurante multiple
6. **Webhooks**: Notificări POS în timp real
7. **Tracking Status Comandă**: Actualizări progres livrare

#### Cale Scalabilitate
```
Curent: Container Docker Unic
    ↓
Faza 1: Bază Date + Redis Cache
    ↓
Faza 2: Servicii Separate (microservicii)
    ├── Serviciu Email (container dedicat)
    ├── Serviciu API (load balanced)
    ├── Serviciu Curățare (cron job)
    └── Bază Date (cluster PostgreSQL)
    ↓
Faza 3: Deployment Kubernetes
    └── Auto-scaling, High Availability
```

---

**Version:** 1.4
**Last Update:** November 26, 2025
**Built with:** Python 3.11, Flask, Gunicorn, IMAPClient, BeautifulSoup4, Docker
