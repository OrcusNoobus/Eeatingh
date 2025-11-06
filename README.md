# 📧 Eeatingh Order Automation System

**Version 1.3** - Complete automated system for processing orders received via email from the eeatingh.ro platform.

## ✨ Features

- ✅ **Real-Time Push Notifications** - Instant processing (1-3 seconds) using IMAP IDLE
- ✅ **Secured REST API** - Endpoints protected with API Key and Rate Limiting
- ✅ **Complete Automatic Cleanup** - Automatically deletes old emails + old JSON files
- ✅ **Centralized Logging** - All logs in `logs/app.log`
- ✅ **Production Server** - Gunicorn WSGI server (not Flask development server)
- ✅ **Docker Deployment** - Optimized for production
- ✅ **Security** - API Key authentication, Rate Limiting, Fail2Ban ready
- ✅ **Single Entry Point** - One command starts all services

## 🚀 Quick Installation

### Docker (Production)

```bash
# 1. Configure credentials in .env (see below)

# 2. Build and start
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop
docker-compose down
```

## ⚙️ Configuration

### .env File

Create/edit the `.env` file:

```env
# Gmail Account (for reading emails)
EMAIL_USER="your-email@gmail.com"
EMAIL_PASS="your-app-password"  # App Password, NOT Gmail password

# Email for error notifications
NOTIFICATION_RECIPIENT="admin@example.com"

# API Security (optional but recommended)
API_KEY="your-secret-api-key-here"
```

### 🔐 Getting Gmail App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to **App passwords**
4. Generate new password for "Mail"
5. Copy the password to `.env`

## 📁 Project Structure

```
Eeatingh/
├── wsgi.py                    # ⭐ ENTRY POINT (WSGI for Gunicorn)
├── app/                       # 📦 Application code
│   ├── __init__.py
│   ├── config.py              # Centralized configuration
│   ├── logging_config.py      # Centralized logging
│   ├── api_server.py          # REST API for integration
│   └── services/              # Application services
│       ├── __init__.py
│       ├── email_listener.py  # Email monitoring (IMAP IDLE + cleanup)
│       ├── order_service.py   # Order processing
│       ├── cleanup_service.py # Automatic file cleanup
│       └── notification_service.py  # Email notifications
├── .env                       # Configuration (credentials)
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker orchestration
├── comenzi/                   # Order folders
│   ├── noi/                   # New orders (for POS)
│   ├── procesate/             # Confirmed orders
│   └── anulate/               # Cancelled orders
└── logs/
    └── app.log                # Centralized logs
```

## 💻 How It Works

### What Does the Application Do?

1. **Email Listener** continuously monitors Gmail inbox using IMAP IDLE
2. When a new email arrives from royalmures@gmail.com, it processes it **instantly**
3. Extracts order data (products, client, address, etc.)
4. Generates JSON file in `comenzi/noi/`
5. Every 15 orders, automatically deletes old emails (>3 days)
6. **Cleanup Service** automatically deletes old JSON files (>7 days) every 24h
7. **API Server** (Gunicorn) exposes orders to external systems (POS)
8. **Security**: All important endpoints are protected with API Key

### Starting the Application

**Production (Docker):**
```bash
docker-compose up -d
```

**Expected output (in logs):**
```
🚀 Starting background services
📧 Starting Email Listener...
🧹 Starting Cleanup Service...
✅ Background services started successfully!
```

**Check status:**
```bash
# View logs in real-time
docker-compose logs -f

# Check if container is running
docker-compose ps
```

### Complete Automation

- ✅ **Email processing**: Automatic, real-time (IMAP IDLE)
- ✅ **Email cleanup**: Automatic, every 15 orders (>3 days)
- ✅ **File cleanup**: Automatic, every 24h (>7 days history)
- ✅ **Reconnection**: Automatic on connection loss
- ✅ **Service restart**: Automatic in case of error
- ✅ **API Security**: API Key authentication + Rate Limiting

## 🔌 API Endpoints

**🔐 Important Note:** Most endpoints require authentication with API Key!

Add the header in all requests:
```http
X-API-Key: your-secret-api-key
```

### 1. Orders (Unified Endpoint) 🔒

**GET** - Retrieve the next unprocessed order:
```http
GET http://localhost:5550/api/comenzi
X-API-Key: your-secret-api-key
```

Returns the first order with `status_comanda: "processing"` (as per POSnet requirements).

**POST** - Confirm or cancel an order:
```http
POST http://localhost:5550/api/comenzi
Content-Type: application/json
X-API-Key: your-secret-api-key

{
  "id_comanda": "6458",
  "operatiune": "CONFIRMA",  // or "ANULEAZA"
  "timp_livrare": 60          // optional
}
```

### 2. Specific Order 🔒
```http
GET http://localhost:5550/api/comanda/6458
X-API-Key: your-secret-api-key
```

### 3. Statistics 🔒
```http
GET http://localhost:5550/api/statistici
X-API-Key: your-secret-api-key
```

### 4. Health Check (Public - no authentication)
```http
GET http://localhost:5550/api/health
```

## 🐳 Docker Deployment

### Deployment on Server (VPS/Contabo)

```bash
# 1. Copy project to server
scp -r Eeatingh/ user@your-server:/opt/

# 2. Connect to server
ssh user@your-server

# 3. Navigate to directory
cd /opt/Eeatingh

# 4. Build and start
docker-compose up -d

# 5. View logs in real-time
docker-compose logs -f

# 6. Check status
docker-compose ps
```

### Useful Docker Commands

```bash
# Restart
docker-compose restart

# Rebuild after changes
docker-compose up -d --build

# Stop
docker-compose down

# View logs
docker-compose logs -f
```

## 📊 Monitoring & Logs

All services write to the same centralized log file:

```bash
# View logs in real-time
tail -f logs/app.log

# Last 100 lines
tail -n 100 logs/app.log

# Search for errors
grep "ERROR" logs/app.log
```

## 🔧 Troubleshooting

### Error: "Authentication failed"
- Check credentials in `.env`
- Make sure you're using **App Password**, not Gmail password
- Verify that 2-Step Verification is enabled

### Application not processing emails
- Check logs: `tail -f logs/app.log`
- Verify sender is `royalmures@gmail.com`
- Test connection: send a test email

### Port 5550 already in use
```bash
# Find the process
lsof -i :5550

# Stop the process
kill -9 <PID>
```

### Docker: Container stops
```bash
# View logs for errors
docker-compose logs

# Rebuild image
docker-compose up -d --build
```

## 📝 Generated JSON Structure

Example JSON generated for POS:

```json
{
  "id_intern_comanda": "6458",
  "simbol_monetar": "RON",
  "email_client": "royalmures@gmail.com",
  "numar_telefon_client": "+40755452101",
  "nume_client": "Incze Imola Blanka",
  "tip_comanda": "livrare",
  "adresa_livrare_client": "Strada Baraganului 61, Targu Mures",
  "valoare_comanda": "201.60",
  "status_comanda": "processing",
  "mod_plata": "CASH",
  "observatii_comanda": "Va rog sunati cand ajungeti",
  "data_comanda": "2025-10-18 18:00:00",
  "produse_comanda": [
    {
      "id_produs": null,
      "denumire_produs": "Paste Bolognese - Standard",
      "cantitate_produs": 1,
      "pret_produs": "34.90",
      "observatii_produs": "",
      "extra": []
    }
  ]
}
```

**Note:** All text data (client name, address, product names, notes) is automatically normalized without diacritics for maximum compatibility with POS systems.

## 🎯 Complete Workflow

1. **Start application**: `docker-compose up -d`
2. Application automatically starts 3 services:
   - **Email Listener** - Email monitoring IMAP IDLE
   - **API Server** - Gunicorn on port 5550
   - **Cleanup Service** - Automatic old file cleanup
3. When a new order arrives:
   - Email Listener detects it instantly (1-3 sec)
   - Processes email and generates JSON in `comenzi/noi/`
   - Counts the processed order
4. POS system retrieves the order:
   - Calls `GET /api/comenzi` (with API Key)
   - Retrieves order data
   - Confirms/cancels with `POST /api/comenzi` (with API Key)
5. Automatic cleanups:
   - **Emails**: Every 15 orders (>3 days)
   - **JSON files**: Every 24h (>7 days history)
6. Everything is logged in `logs/app.log`

## 🔒 Security

### Implemented Security Features

- ✅ **API Key Authentication** - All important endpoints are protected
- ✅ **Rate Limiting** - 100 requests/minute per IP (prevents brute-force)
- ✅ **Gunicorn Production Server** - Professional WSGI server, not development server
- ✅ **Fail2Ban Ready** - Structured logs for Fail2Ban integration
- ✅ **Credentials in .env** - Not committed to Git
- ✅ **Gmail App Password** - Not real password
- ✅ **Docker Isolation** - Application runs isolated

### Quick Security Setup

1. **Generate API Key:**
```bash
openssl rand -hex 32
```

2. **Add to `.env`:**
```env
API_KEY="generated-key-above"
```

3. **Restart application:**
```bash
docker-compose restart
```

### Recommended Security Architecture (Production)

```
Internet → Nginx (SSL + Fail2Ban) → Gunicorn (API Key + Rate Limit) → Application
```

- **Nginx**: Reverse proxy with SSL/TLS, rate limiting, security headers
- **Fail2Ban**: Blocks IPs after failed attempts
- **Gunicorn**: Production server with multi-worker support
- **API Key**: Application-level authentication
- **Rate Limiting**: Protection against abuse

## 📞 Support

For issues:
1. Check logs: `logs/app.log`
2. Check settings in `.env`
3. Test with manual email
4. Verify internet connection

## 📄 License

Private Property - Royal Food Delivery

## 🌐 Language Support

- **English Documentation**: `README.md` (this file)
- **Romanian Documentation**: `README_RO.md`

## 🆕 What's New in Version 1.3

### Enhanced API
- ✅ **Unified Endpoint `/api/comenzi`** - Same route for GET and POST
- ✅ **JSON Key Order Preservation** - Exact order from model for POSnet
- ✅ API simplification and clarification

### Technical Improvements
- ✅ `app.json.sort_keys = False` for maximum compatibility
- ✅ Code refactoring for maintainability
- ✅ Complete documentation update

---

**Version:** 1.3  
**Last Update:** November 6, 2025  
**Improvements:** Unified endpoint, JSON order preservation, Senior-level code refinement

**Built with:** Python 3.11, Flask, Gunicorn, IMAPClient, BeautifulSoup4, Docker
