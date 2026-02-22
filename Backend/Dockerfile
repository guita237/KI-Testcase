# Offizielles Python 3.10-Slim-Image nutzen
FROM python:3.10-slim

# Arbeitsverzeichnis im Container setzen
WORKDIR /app

# Nur requirements.txt zuerst kopieren (für Docker-Cache)
COPY requirements.txt .

# System-Tools installieren, falls nötig (z.B. für Transformers oder Torch)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Pip & Abhängigkeiten installieren
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Flask-Umgebungsvariablen setzen
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Port öffnen
EXPOSE 5000

# App mit Gunicorn starten
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120",  "main:app"]
