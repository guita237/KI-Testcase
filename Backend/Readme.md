# KI-gestütztes Testmanagement – Backend (Flask)

Ein KI-gestütztes Backend für automatisiertes Softwaretestmanagement. Entwickelt mit **Flask**, **SQLAlchemy** und **PostgreSQL**. Das System nutzt **OpenAI GPT-4o-mini**, **Sentence Transformers** und **scikit-learn** zur automatischen Testfallgenerierung, Priorisierung, Redundanzerkennung und Testautomatisierung. Authentifizierung erfolgt über **Firebase**.

---

## Inhaltsverzeichnis

- [Technologien](#technologien)
- [Projektstruktur](#projektstruktur)
- [Datenmodell](#datenmodell)
- [KI-Module](#ki-module)
- [Docker](#docker)
- [Konfiguration](#konfiguration)
- [Verwendung](#verwendung)

---

## Technologien

- **Python 3.10**
- **Flask 3.1** + **Flask-SQLAlchemy** + **Flask-Migrate**
- **PostgreSQL 14** (via `psycopg2`)
- **Gunicorn** (WSGI-Server, 4 Worker)
- **Firebase Admin SDK** – Authentifizierung & Token-Verifizierung
- **OpenAI API** (`gpt-4o-mini`) – Testfallgenerierung & Priorisierung
- **Sentence Transformers** (`paraphrase-multilingual-MiniLM-L12-v2`) – RAG-Ähnlichkeitssuche
- **scikit-learn** – ML-Modell (Random Forest), TF-IDF, Cosinus-Ähnlichkeit
- **nginx** – Reverse Proxy mit langen Timeouts für KI-Anfragen (600s)
- **Docker** + **Docker Compose**

---

## Projektstruktur

```
Backend/
├── app/
│   ├── __init__.py              # App-Factory: Flask, SQLAlchemy, Migrate, Blueprint
│   ├── config.py                # Konfiguration: DB-URL, Secret Key (aus .env)
│   ├── models.py                # SQLAlchemy-Modelle (5 KB)
│   ├── routes/                  # API-Routen (Blueprint)
│   ├── templates/               # Jinja2-Templates (falls nötig)
│   ├── rag_docs/                # RAG-Dokumente (txt/md) für Kontextsuche
│   │   ├── sicherheit/
│   │   │   ├── passwortrichtlinie.txt
│   │   │   └── 2fa_policy.md
│   │   └── ui/
│   │       └── login_standard.txt
│   └── utils/
│       ├── __init__.py          # Utility-Exports & Firebase-Initialisierung
│       ├── firebase.py          # Firebase-Init & Token-Verifikation
│       ├── sendmail.py          # E-Mail-Versand (Verify, Reset, Modify)
│       ├── nlp_utils.py         # OpenAI + RAG + NLP-Funktionen
│       ├── ml_utils.py          # ML-Modell (Random Forest, TF-IDF)
│       └── datei_typ.py         # Dateiextraktion (PDF, DOCX, XLSX)
│
├── Firebase/                    # Firebase Service Account Key
├── generated_scripts/           # Automatisch generierte Testskripte
├── migrations/                  # Alembic DB-Migrationen
├── Test/                        # Pytest-Tests
├── main.py                      # Flask-Einstiegspunkt
├── requirements.txt             # Python-Abhängigkeiten
├── Dockerfile                   # Container-Build
├── docker-compose.example       # Docker Compose Vorlage
├── Dockerfile.example           # Dockerfile Vorlage
├── nginx.conf.example           # nginx-Konfiguration Vorlage
└── .env                         # Umgebungsvariablen (nicht im Git)
```

---

## Datenmodell

```
User ──< Project ──< TestCase ──< KISuggestion
  │                     │
  └──< Log          RAGReference (Embedding-Datenbank)
                    CodeChange
```

| Modell | Beschreibung |
|---|---|
| `User` | Benutzer mit Rolle (`admin` / `tester`), Firebase-ID |
| `Project` | Projekt mit Namen, Beschreibung, erstellt von User |
| `TestCase` | Testfall mit Kategorie, Priorität, Testskript, Anforderungstext, Redundanzstatus |
| `KISuggestion` | KI-generierter Vorschlag (Priorisierung, Generierung) |
| `CodeChange` | Codeänderungen (Dateiname, Zeilen, Commit-ID) |
| `RAGReference` | Embedding-Datenbank: Anforderung → Testfall + Kategorie + Vektor |
| `Log` | Aktionsprotokoll pro Benutzer |

---

## KI-Module

### `nlp_utils.py` – NLP & OpenAI

| Funktion | Beschreibung |
|---|---|
| `generate_test_cases(requirements_text)` | Generiert 5 Testfälle pro Anforderung via GPT (**Streaming**) |
| `generate_summary(text)` | Erstellt eine Zusammenfassung via GPT |
| `find_redundant_test_cases(test_cases)` | Erkennt redundante Testfälle via GPT (**Streaming**) |
| `classify_requirements(text)` | Klassifiziert eine Anforderung (funktional / nicht-funktional) |
| `classify_multiple_requirements(list)` | Batch-Klassifikation mehrerer Anforderungen |
| `prioritize_test_cases(test_cases)` | Priorisiert Testfälle (hoch/mittel/niedrig) via GPT (**Streaming**) |
| `generate_test_script(description, framework)` | Generiert Testcode (pytest/selenium) via GPT (**Streaming**) |
| `generiere_testfälle(anforderung)` | Generiert Testfälle mit RAG-Kontext |
| `load_rag_files(config)` | Lädt RAG-Dokumente aus Dateien |

**RAG-Suche** (`multi_rag_suche_complet`): Kombiniert dateibasierte Suche (Cosinus-Ähnlichkeit via SentenceTransformer) mit Datenbanksuche (`RAGReference`) für kontextbewusste Testfallgenerierung.

### `ml_utils.py` – Machine Learning

| Funktion | Beschreibung |
|---|---|
| `train_and_save_model(test_cases, labels)` | Trainiert Random Forest + TF-IDF und speichert Modell |
| `predict_category(text)` | Klassifiziert Testfall (funktional / nicht-funktional) |
| `find_redundant_tests_ml(test_cases)` | ML-basierte Redundanzerkennung |
| `prioritize_test_cases_with_ml(test_cases)` | ML-basierte Priorisierung (niedrig/mittel/hoch) |
| `simple_prioritize_test_cases(test_cases)` | Heuristische Priorisierung (Risiko, Komplexität, Impact) |
| `sentiment_analysis(text)` | Stimmungsanalyse (positiv/neutral/negativ) |

### `datei_typ.py` – Dateiextraktion

| Funktion | Unterstütztes Format |
|---|---|
| `extract_text_from_pdf(path)` | PDF (via `pdfminer.six`) |
| `extract_text_from_docx(path)` | Word DOCX (via `python-docx`) |
| `extract_text_from_xlsx(path)` | Excel XLSX (via `xlrd`) |

### `firebase.py` – Authentifizierung

- `initialize_firebase()` – Initialisiert Firebase Admin SDK über Credentials-Datei
- `verify_token(token)` – Verifiziert Firebase ID-Token

### `sendmail.py` – E-Mail-Versand (SMTP)

| Funktion | Beschreibung |
|---|---|
| `send_verification_email(name, email, link)` | E-Mail-Verifizierung beim Registrieren |
| `send_reset_password(name, email, link)` | Passwort-Zurücksetzen |
| `send_modification_email(name, email, link)` | Bestätigung bei E-Mail-Änderung |

Alle E-Mails verwenden **HTML-Templates** im Blau-Design mit responsivem Layout.

---

## Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "main:app"]
```

### docker-compose (Kurzversion)

```
PostgreSQL (healthy) ──▶ Flask/Gunicorn ──▶ nginx (Port 80)
```

- **PostgreSQL 14** mit persistentem Volume
- **Flask** startet erst wenn DB healthy ist (`flask db upgrade` → `gunicorn`)
- **nginx** leitet alle Anfragen an Flask weiter, mit **600s Timeout** für KI-Operationen
- `sentence_transformer_cache` Volume für Modell-Cache

---

## Konfiguration

Kopiere `docker-compose.example` → `docker-compose.yml` und `nginx.conf.example` → `nginx.conf`, dann `.env` befüllen:

```env
# Datenbank
DATABASE_URL=postgresql://user:password@db:5432/dbname
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=dbname

# Flask
FLASK_SECRET_KEY=your_secret_key

# Firebase
FIREBASE_CREDENTIALS_PATH=/app/Firebase/serviceAccount.json
FIREBASE_API_KEY=your_firebase_api_key

# OpenAI
OPENAI_API_KEY=sk-...

# E-Mail (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_EMAIL=app@example.com
SMTP_PASSWORD=your_email_password
APP_NAME=YourAppName
```

---

## Verwendung

### Mit Docker
```bash
cp docker-compose.example docker-compose.yml
cp nginx.conf.example nginx.conf
# .env befüllen
docker compose up --build
```

API erreichbar unter: `http://localhost:80`

### Lokal (ohne Docker)
```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
flask db upgrade             # DB-Migrationen anwenden
flask run                    # Dev-Server starten
```

### Tests ausführen
```bash
pytest Test/
```

> Healthcheck-Endpunkt: `GET /health` → `{"status": "healthy"}`