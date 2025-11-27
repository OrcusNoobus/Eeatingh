# 📧 Sistem Automatizare Comenzi Eeatingh

**Versiunea 1.3** - Sistem complet automatizat pentru procesarea comenzilor primite prin email de la platforma eeatingh.ro.

## ✨ Caracteristici

- ✅ **Notificări Push în Timp Real** - Procesare instant (1-3 secunde) folosind IMAP IDLE
- ✅ **API REST Securizat** - Endpoints protejate cu API Key și Rate Limiting
- ✅ **Curățare Automată Completă** - Șterge emailuri vechi + fișiere JSON vechi automat
- ✅ **Logging Centralizat** - Toate log-urile în `logs/app.log`
- ✅ **Server de Producție** - Gunicorn WSGI server (nu Flask development server)
- ✅ **Deployment Docker** - Optimizat pentru producție
- ✅ **Securitate** - Autentificare API Key, Rate Limiting, Fail2Ban ready
- ✅ **Punctul Unic de Pornire** - O singură comandă pornește toate serviciile

## 🚀 Instalare Rapidă

### Docker (Producție)

```bash
# 1. Configurează credențialele în .env (vezi mai jos)

# 2. Build și start
docker-compose up -d

# 3. Vezi logs
docker-compose logs -f

# 4. Oprire
docker-compose down
```

## ⚙️ Configurare

### Fișier .env

Creează/editează fișierul `.env`:

```env
# Gmail Account (pentru citire emailuri)
EMAIL_USER="your-email@gmail.com"
EMAIL_PASS="your-app-password"  # App Password, NU parola Gmail

# Email notificări erori
NOTIFICATION_RECIPIENT="admin@example.com"
```

### 🔐 Obținere App Password Gmail

1. Accesează [Google Account Security](https://myaccount.google.com/security)
2. Activează **2-Step Verification**
3. Mergi la **App passwords**
4. Generează password nou pentru "Mail"
5. Copiază password-ul în `.env`

## 📁 Structura Proiectului

```
Eeatingh/
├── wsgi.py                    # ⭐ PUNCT DE PORNIRE (WSGI pentru Gunicorn)
├── app/                       # 📦 Codul aplicației
│   ├── __init__.py
│   ├── config.py              # Configurare centralizată
│   ├── logging_config.py      # Logging centralizat
│   ├── api_server.py          # API REST pentru integrare
│   └── services/              # Servicii aplicație
│       ├── __init__.py
│       ├── email_listener.py  # Monitoring emailuri (IMAP IDLE + cleanup)
│       ├── order_service.py   # Procesare comenzi
│       ├── cleanup_service.py # Curățare automată fișiere
│       └── notification_service.py  # Notificări email
├── .env                       # Configurări (credentials)
├── requirements.txt           # Dependențe Python
├── Dockerfile                 # Configurare Docker
├── docker-compose.yml         # Orchestrare Docker
├── comenzi/                   # Foldere pentru comenzi
│   ├── noi/                   # Comenzi noi (pentru POSnet)
│   ├── procesate/             # Comenzi confirmate
│   └── anulate/               # Comenzi anulate
└── logs/
    └── app.log                # Log-uri centralizate
```

## 💻 Cum Funcționează

### Ce Face Aplicația?

1. **Email Listener** monitorizează continuu inbox-ul Gmail folosind IMAP IDLE
2. Când sosește un email nou de la royalmures@gmail.com, îl procesează **instant**
3. Extrage datele comenzii (produse, client, adresă, etc.)
4. Generează fișier JSON în `comenzi/noi/`
5. La fiecare 15 comenzi, șterge automat emailurile vechi (>3 zile)
6. **Cleanup Service** șterge automat fișierele JSON vechi (>7 zile) la fiecare 24h
7. **API Server** (Gunicorn) expune comenzile pentru sisteme externe (POS)
8. **Securitate**: Toate endpoint-urile importante sunt protejate cu API Key

### Pornire Aplicație

**Producție (Docker):**
```bash
docker-compose up -d
```

**Output așteptat (în logs):**
```
🚀 Pornire servicii background
📧 Pornire Email Listener...
🧹 Pornire Cleanup Service...
✅ Servicii background pornite cu succes!
```

**Verificare status:**
```bash
# Vezi logs în timp real
docker-compose logs -f

# Verifică dacă containerul rulează
docker-compose ps
```

### Automatizare Completă

- ✅ **Procesare emailuri**: Automată, în timp real (IMAP IDLE)
- ✅ **Curățare emailuri**: Automată, la fiecare 15 comenzi (>3 zile)
- ✅ **Curățare fișiere**: Automată, la fiecare 24h (>7 zile istoric)
- ✅ **Reconectare**: Automată la pierderea conexiunii
- ✅ **Restart servicii**: Automat în caz de eroare
- ✅ **Securitate API**: Autentificare cu API Key + Rate Limiting

## 🔌 API Endpoints

**🔐 Notă Importantă:** Majoritatea endpoint-urilor necesită autentificare cu API Key!

Adaugă header-ul în toate request-urile:
```http
X-API-Key: your-secret-api-key
```

### 1. Comenzi (Endpoint Unificat) 🔒

**GET** - Preia următoarea comandă neprocesată:
```http
GET http://localhost:5550/api/comenzi
X-API-Key: your-secret-api-key
```

Returnează prima comandă cu `status_comanda: "processing"` (conform cerințelor POSnet).

**POST** - Confirmă sau anulează o comandă:
```http
POST http://localhost:5550/api/comenzi
Content-Type: application/json
X-API-Key: your-secret-api-key

{
  "id_comanda": "6458",
  "operatiune": "CONFIRMA",  // sau "ANULEAZA"
  "timp_livrare": 60          // opțional
}
```

### 2. Comandă Specifică 🔒
```http
GET http://localhost:5550/api/comanda/6458
X-API-Key: your-secret-api-key
```

### 3. Statistici 🔒
```http
GET http://localhost:5550/api/statistici
X-API-Key: your-secret-api-key
```

### 4. Health Check (Public - fără autentificare)
```http
GET http://localhost:5550/api/health
```

**📖 Pentru detalii despre securitate, consultă [README_SECURITY.md](README_SECURITY.md)**

## 🐳 Docker Deployment

### Deployment pe Server (VPS/Contabo)

```bash
# 1. Copiază proiectul pe server
scp -r Eeatingh/ user@your-server:/opt/

# 2. Conectează-te la server
ssh user@your-server

# 3. Navighează în director
cd /opt/Eeatingh

# 4. Build și start
docker-compose up -d

# 5. Vezi logs în timp real
docker-compose logs -f

# 6. Verifică status
docker-compose ps
```

### Comenzi Utile Docker

```bash
# Restart
docker-compose restart

# Rebuild după modificări
docker-compose up -d --build

# Oprire
docker-compose down

# Vezi logs
docker-compose logs -f
```

## 📊 Monitoring & Logs

Toate serviciile scriu în același fișier de log centralizat:

```bash
# Vezi logs în timp real
tail -f logs/app.log

# Ultimele 100 linii
tail -n 100 logs/app.log

# Caută erori
grep "ERROR" logs/app.log
```

## 🔧 Troubleshooting

### Eroare: "Authentication failed"
- Verifică credentialele din `.env`
- Asigură-te că folosești **App Password**, nu parola Gmail
- Verifică că 2-Step Verification este activat

### Aplicația nu procesează emailuri
- Verifică logs: `tail -f logs/app.log`
- Verifică că expeditorul este `royalmures@gmail.com`
- Testează conexiunea: trimite un email de test

### Port 5550 deja în uz
```bash
# Găsește procesul
lsof -i :5550

# Oprește procesul
kill -9 <PID>
```

### Docker: Container se oprește
```bash
# Vezi logs pentru erori
docker-compose logs

# Reconstruiește imaginea
docker-compose up -d --build


## 🎯 Flux de Lucru Complet

1. **Pornește aplicația**: `docker-compose up -d`
2. Aplicația pornește automat 3 servicii:
   - **Email Listener** - Monitorizare emailuri IMAP IDLE
   - **API Server** - Gunicorn pe port 5550
   - **Cleanup Service** - Curățare automată fișiere
3. Când vine o comandă nouă:
   - Email Listener o detectează instant (1-3 sec)
   - Procesează emailul și generează JSON în `comenzi/noi/`
   - Contorizează comanda procesată
4. Sistemul POS preia comanda:
   - Apelează `GET /api/comenzi` (cu API Key)
   - Preia datele comenzii
   - Confirmă/anulează cu `POST /api/comenzi` (cu API Key)
5. Curățări automate:
   - **Emailuri**: La fiecare 15 comenzi (>3 zile)
   - **Fișiere JSON**: La fiecare 24h (>7 zile istoric)
6. Totul se loghează în `logs/app.log`

## 🔒 Securitate

### Caracteristici de Securitate Implementate

- ✅ **Autentificare API Key** - Toate endpoint-urile importante sunt protejate
- ✅ **Rate Limiting** - 100 request-uri/minut per IP (previne brute-force)
- ✅ **Gunicorn Production Server** - Server WSGI profesional, nu development server
- ✅ **Fail2Ban Ready** - Logs structurate pentru integrare cu Fail2Ban
- ✅ **Credentials în .env** - Nu se comit în Git
- ✅ **App Password Gmail** - Nu parola reală
- ✅ **Docker Isolation** - Aplicația rulează izolat

### Setup Rapid Securitate

1. **Generează API Key:**
```bash
openssl rand -hex 32
```

2. **Adaugă în `.env`:**
```env
API_KEY="cheia-generata-mai-sus"
```

3. **Restart aplicația:**
```bash
docker-compose restart
```

**📖 Documentație Completă: [README_SECURITY.md](README_SECURITY.md)**

### Arhitectură Securitate Recomandată (Producție)

```
Internet → Nginx (SSL + Fail2Ban) → Gunicorn (API Key + Rate Limit) → Aplicație
```

- **Nginx**: Reverse proxy cu SSL/TLS, rate limiting, security headers
- **Fail2Ban**: Blochează IP-uri după tentative eșuate
- **Gunicorn**: Server de producție cu multi-worker support
- **API Key**: Autentificare la nivel de aplicație
- **Rate Limiting**: Protecție împotriva abuzului

## 📞 Support

Pentru probleme:
1. Verifică logs: `logs/app.log`
2. Verifică configurările din `.env`
3. Testează cu email manual
4. Verifică conexiunea la internet

## 📄 License

Proprietate privată - Royal Food Delivery

## 📚 Documentație Suplimentară

- **[README_SECURITY.md](README_SECURITY.md)** - Ghid complet de securitate, deployment pe server, configurare Nginx, Fail2Ban, SSL, monitoring

## 🆕 Ce e Nou în Versiunea 1.3

### API Îmbunătățit
- ✅ **Endpoint Unificat `/api/comenzi`** - Aceeași rută pentru GET și POST
- ✅ **Păstrarea Ordinii Cheilor JSON** - Ordinea exactă din model pentru POSnet
- ✅ Simplificare și clarificare API

### Îmbunătățiri Tehnice
- ✅ `app.json.sort_keys = False` pentru compatibilitate maximă
- ✅ Refactorizare cod pentru mentenabilitate
- ✅ Documentație actualizată complet

---

**Versiune:** 1.3  
**Ultima actualizare:** 6 Noiembrie 2025  
**Îmbunătățiri:** Endpoint unificat, Păstrare ordine JSON, Rafinare cod senior-level
