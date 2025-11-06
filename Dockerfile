# Dockerfile pentru sistemul de automatizare comenzi eeatingh
FROM python:3.11-slim

# Setează working directory
WORKDIR /app

# Instalează dependențele de sistem necesare
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiază requirements
COPY requirements.txt .

# Instalează dependențele Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiază codul aplicației
COPY wsgi.py .
COPY gunicorn_config.py .
COPY .env .
COPY app/ ./app/

# Creează directoarele necesare
RUN mkdir -p comenzi/noi comenzi/procesate comenzi/anulate logs

# Setează timezone
ENV TZ=Europe/Bucharest
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Expune portul API
EXPOSE 5550

# Comandă de pornire - folosește Gunicorn cu fișier de configurare
# Configurația este în gunicorn_config.py care:
# - Definește toate setările Gunicorn (bind, workers, threads, etc.)
# - Pornește serviciile de background (Email Listener, Cleanup) în master process
# - Previne duplicarea serviciilor la fiecare worker
CMD ["gunicorn", \
     "--config", "gunicorn_config.py", \
     "wsgi:application"]
