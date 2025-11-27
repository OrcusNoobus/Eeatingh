# 📧 Eeatingh Order Automation System | Sistem Automatizare Comenzi Eeatingh

**Version 1.4** | **Versiunea 1.4**

---

## 🇺🇸 English Documentation

Complete automated system for processing orders received via email from the eeatingh.ro platform.

### ✨ Features

- ✅ **Real-Time Push Notifications** - Instant processing (1-3 seconds) using IMAP IDLE
- ✅ **Intelligent HTML Parsing** - Content-based detection (not position-based) for robust parsing
- ✅ **Secured REST API** - Endpoints protected with API Key and Rate Limiting
- ✅ **Complete Automatic Cleanup** - Automatically deletes old emails + old JSON files
- ✅ **Centralized Logging** - All logs in `logs/app.log`
- ✅ **Production Server** - Gunicorn WSGI server (not Flask development server)
- ✅ **Docker Deployment** - Optimized for production
- ✅ **Security** - API Key authentication, Rate Limiting, Fail2Ban ready
- ✅ **Single Entry Point** - One command starts all services

### 🚀 Quick Installation

#### Docker (Production)

```bash
# 1. Configure credentials in .env
cp .env.example .env
nano .env

# 2. Build and start
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop
docker-compose down
```

### ⚙️ Configuration

Create/edit the `.env` file:

```env
# Gmail Account (for reading emails)
EMAIL_USER="your-email@gmail.com"
EMAIL_PASS="your-app-password"  # App Password, NOT Gmail password

# Email for error notifications
NOTIFICATION_RECIPIENT="admin@example.com"

# API Security (recommended)
API_KEY="your-secret-api-key-here"
```

#### 🔐 Getting Gmail App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to **App passwords**
4. Generate new password for "Mail"
5. Copy the password to `.env`

### 📁 Project Structure

```
Eeatingh/
├── wsgi.py                    # ⭐ ENTRY POINT
├── app/
│   ├── api_server.py          # REST API
│   ├── config.py              # Configuration
│   ├── logging_config.py      # Logging
│   └── services/
│       ├── email_listener.py  # Email monitoring (IMAP IDLE)
│       ├── order_service.py   # Smart order parsing
│       ├── cleanup_service.py # Automatic cleanup
│       └── notification_service.py
├── comenzi/                   # Orders
│   ├── noi/                   # New orders
│   ├── procesate/             # Processed orders
│   └── anulate/               # Cancelled orders
├── logs/app.log               # Centralized logs
├── modificari.md              # Recent changes (v1.4)
├── architecture.md            # System architecture
└── docker-compose.yml
```

### 🔌 API Endpoints

**🔐 Important:** Most endpoints require API Key authentication!

Add header to all requests:
```http
X-API-Key: your-secret-api-key
```

#### GET /api/comenzi 🔒
Retrieve the next unprocessed order.

#### POST /api/comenzi 🔒
Confirm or cancel an order.

```json
{
  "id_comanda": "6458",
  "operatiune": "CONFIRMA",
  "timp_livrare": 60
}
```

#### GET /api/comanda/{id} 🔒
Get specific order details.

#### GET /api/statistici 🔒
Get order statistics.

#### GET /api/health
Health check (public, no auth required).

### 🆕 What's New in Version 1.4

#### Critical Bug Fixes
- ✅ **Smart HTML Parsing** - Content-based detection instead of position-based
  - Handles missing client names gracefully
  - Phone number detection with regex patterns
  - Address detection using keywords + Google Maps links
  - Payment method detection (CASH, POS, CARD, ramburs)
- ✅ **Word Boundary Protection** - Prevents false matches (e.g., "ap" in "Pap")
- ✅ **Robust Payment Detection** - Skips headers, detects all payment types

#### Testing
All edge cases tested and working:
- Orders without client name ✅
- Orders with POS/ramburs payment ✅
- Various HTML structures ✅

For detailed technical explanation, see [modificari.md](modificari.md)

### 🐳 Docker Deployment

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down
```

### 📊 Monitoring

```bash
# Real-time logs
tail -f logs/app.log

# Search errors
grep "ERROR" logs/app.log
```

### 🔒 Security

- **API Key Authentication** - Protect all endpoints
- **Rate Limiting** - 100 requests/minute per IP
- **Gunicorn Production Server** - Professional WSGI
- **Fail2Ban Ready** - Structured logs
- **Docker Isolation** - Containerized environment

Generate API Key:
```bash
openssl rand -hex 32
```

### 📖 Documentation

- **[architecture.md](architecture.md)** - System architecture and design
- **[modificari.md](modificari.md)** - Recent changes and bug fixes (v1.4)

---

## 🇷🇴 Documentație în Limba Română

Sistem complet automatizat pentru procesarea comenzilor primite prin email de la platforma eeatingh.ro.

### ✨ Caracteristici

- ✅ **Notificări Push în Timp Real** - Procesare instant (1-3 secunde) folosind IMAP IDLE
- ✅ **Parsare HTML Inteligentă** - Detectare bazată pe conținut (nu pe poziție) pentru parsare robustă
- ✅ **API REST Securizat** - Endpoints protejate cu API Key și Rate Limiting
- ✅ **Curățare Automată Completă** - Șterge emailuri vechi + fișiere JSON vechi automat
- ✅ **Logging Centralizat** - Toate log-urile în `logs/app.log`
- ✅ **Server de Producție** - Gunicorn WSGI server (nu Flask development server)
- ✅ **Deployment Docker** - Optimizat pentru producție
- ✅ **Securitate** - Autentificare API Key, Rate Limiting, Fail2Ban ready
- ✅ **Punctul Unic de Pornire** - O singură comandă pornește toate serviciile

### 🚀 Instalare Rapidă

#### Docker (Producție)

```bash
# 1. Configurează credențialele în .env
cp .env.example .env
nano .env

# 2. Build și start
docker-compose up -d

# 3. Vezi logs
docker-compose logs -f

# 4. Oprire
docker-compose down
```

### ⚙️ Configurare

Creează/editează fișierul `.env`:

```env
# Gmail Account (pentru citire emailuri)
EMAIL_USER="your-email@gmail.com"
EMAIL_PASS="your-app-password"  # App Password, NU parola Gmail

# Email notificări erori
NOTIFICATION_RECIPIENT="admin@example.com"

# API Security (recomandat)
API_KEY="your-secret-api-key-here"
```

#### 🔐 Obținere App Password Gmail

1. Accesează [Google Account Security](https://myaccount.google.com/security)
2. Activează **2-Step Verification**
3. Mergi la **App passwords**
4. Generează password nou pentru "Mail"
5. Copiază password-ul în `.env`

### 📁 Structura Proiectului

```
Eeatingh/
├── wsgi.py                    # ⭐ PUNCT DE PORNIRE
├── app/
│   ├── api_server.py          # API REST
│   ├── config.py              # Configurare
│   ├── logging_config.py      # Logging
│   └── services/
│       ├── email_listener.py  # Monitoring emailuri (IMAP IDLE)
│       ├── order_service.py   # Parsare inteligentă comenzi
│       ├── cleanup_service.py # Curățare automată
│       └── notification_service.py
├── comenzi/                   # Comenzi
│   ├── noi/                   # Comenzi noi
│   ├── procesate/             # Comenzi procesate
│   └── anulate/               # Comenzi anulate
├── logs/app.log               # Log-uri centralizate
├── modificari.md              # Modificări recente (v1.4)
├── architecture.md            # Arhitectura sistemului
└── docker-compose.yml
```

### 🔌 API Endpoints

**🔐 Important:** Majoritatea endpoint-urilor necesită autentificare cu API Key!

Adaugă header în toate request-urile:
```http
X-API-Key: your-secret-api-key
```

#### GET /api/comenzi 🔒
Preia următoarea comandă neprocesată.

#### POST /api/comenzi 🔒
Confirmă sau anulează o comandă.

```json
{
  "id_comanda": "6458",
  "operatiune": "CONFIRMA",
  "timp_livrare": 60
}
```

#### GET /api/comanda/{id} 🔒
Obține detaliile unei comenzi specifice.

#### GET /api/statistici 🔒
Obține statistici comenzi.

#### GET /api/health
Health check (public, fără autentificare).

### 🆕 Ce e Nou în Versiunea 1.4

#### Rezolvări Bug-uri Critice
- ✅ **Parsare HTML Inteligentă** - Detectare bazată pe conținut în loc de poziție
  - Gestionează elegant lipsa numelui clientului
  - Detectare număr telefon cu pattern-uri regex
  - Detectare adresă folosind cuvinte cheie + link-uri Google Maps
  - Detectare mod plată (CASH, POS, CARD, ramburs)
- ✅ **Protecție Word Boundary** - Previne potriviri false (ex: "ap" în "Pap")
- ✅ **Detectare Robustă Mod Plată** - Ignoră header-e, detectează toate tipurile de plată

#### Testare
Toate cazurile limită testate și funcționale:
- Comenzi fără nume client ✅
- Comenzi cu plată POS/ramburs ✅
- Structuri HTML variate ✅

Pentru explicație tehnică detaliată, vezi [modificari.md](modificari.md)

### 🐳 Docker Deployment

```bash
# Pornire
docker-compose up -d

# Vezi logs
docker-compose logs -f

# Restart
docker-compose restart

# Oprire
docker-compose down
```

### 📊 Monitoring

```bash
# Logs în timp real
tail -f logs/app.log

# Caută erori
grep "ERROR" logs/app.log
```

### 🔒 Securitate

- **Autentificare API Key** - Protejează toate endpoint-urile
- **Rate Limiting** - 100 request-uri/minut per IP
- **Gunicorn Production Server** - WSGI profesional
- **Fail2Ban Ready** - Log-uri structurate
- **Izolare Docker** - Environment containerizat

Generează API Key:
```bash
openssl rand -hex 32
```

### 📖 Documentație

- **[architecture.md](architecture.md)** - Arhitectura și design-ul sistemului
- **[modificari.md](modificari.md)** - Modificări recente și rezolvări bug-uri (v1.4)

---

**Version:** 1.4
**Last Update:** November 26, 2025
**Improvements:** Intelligent HTML parsing, robust payment detection, comprehensive bug fixes

**Built with:** Python 3.11, Flask, Gunicorn, IMAPClient, BeautifulSoup4, Docker

## 📄 License

Private Property - Royal Food Delivery
