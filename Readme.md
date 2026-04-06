# KI-gestütztes Testmanagement – Gesamtprojekt

## Automatisierte Testfallgenerierung mit LLM, RAG und React

Dieses Projekt entstand im Rahmen der Bachelorarbeit **"KI-gestützte Automatisierung von Softwaretests: Effizienzsteigerung durch Machine Learning und Natural Language Processing"** an der Hochschule Darmstadt.

Ziel ist die automatische Generierung von Testfällen aus natürlichsprachlichen Softwareanforderungen mithilfe Künstlicher Intelligenz. Der Prototyp kombiniert **Large Language Models (LLMs)** mit **Retrieval-Augmented Generation (RAG)** und einer **React-basierten Weboberfläche**.

---

## 📋 Inhaltsverzeichnis

- [Über das Projekt](#über-das-projekt)
- [Architekturübersicht](#architekturübersicht)
- [Technologien](#technologien)
- [Projektstruktur](#projektstruktur)
- [KI-Kernfunktionen](#ki-kernfunktionen)
- [Voraussetzungen](#voraussetzungen)
- [Installation & Start](#installation--start)
- [Docker Compose (Empfohlen)](#docker-compose-empfohlen)
- [Umgebungskonfiguration](#umgebungskonfiguration)
- [Screenshots](#screenshots)
- [Forschungsfragen & Ergebnisse](#forschungsfragen--ergebnisse)
- [Fazit & Ausblick](#fazit--ausblick)


---

## Über das Projekt

Das System ermöglicht es QA-Ingenieuren und Entwicklern, aus textuellen Anforderungen automatisch strukturierte Testfälle zu generieren. Besondere Merkmale sind:

- **Semantische Kontextanreicherung** durch RAG (Dokumente + Datenbank)
- **Automatische Klärungslogik** bei unvollständigen Anforderungen
- **Unterstützung von Classic- und BDD-Formaten** (Gherkin)
- **Modulare Architektur** mit Flask-Backend und React-Frontend
- **Docker-Containerisierung** für einfache Bereitstellung

---

## Architekturübersicht
```
┌─────────────────────────────────────────────────────────────────┐
│ Benutzer (Browser) │
└─────────────────────────────────┬───────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (React + Nginx) │
│ Port: 80 (Produktion) / 5173 (Dev) │
└─────────────────────────────────┬───────────────────────────────┘
│ /api/
▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend (Flask + Gunicorn) │
│ Port: 5000 │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│ │ Routes      │ │  Services   │ │        KI-Module        │ │
│ │ - /auth     │ │ - auth      │ │ - RAG (Dateien + DB)    │ │
│ │ - /projects │ │ - projects  │ │ - OpenAI GPT-4o-mini    │ │
│ │ - /test     │ │ - test_case │ │ - SentenceTransformer   │ │
│ │ - /ai       │ │ - logs      │ │ - Klärungslogik         │ │
│ │ - /logs     │ │ - ki_suggest│ │ - Formatvalidierung     │ │
│ └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────┬───────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ PostgreSQL (Datenbank) │
│ Port: 5432 │
│ Tabellen: user, project, test_case, log, ki_suggestion, │
│ rag_reference, code_change │
└─────────────────────────────────────────────────────────────────┘

```

---

## Technologien

### Backend
| Kategorie | Technologien |
|-----------|--------------|
| **Framework** | Python 3.10, Flask 3.1 |
| **ORM** | Flask-SQLAlchemy, Flask-Migrate |
| **Datenbank** | PostgreSQL 14 |
| **LLM-Integration** | OpenAI API (GPT-4o-mini) |
| **Embeddings** | SentenceTransformer (paraphrase-multilingual-MiniLM-L12-v2) |
| **Ähnlichkeit** | Cosine Similarity (scikit-learn) |
| **Authentifizierung** | Firebase Admin SDK |
| **E-Mail** | SMTP (Verifikation, Reset, Änderung) |
| **WSGI** | Gunicorn (4 Worker, 120s Timeout) |

### Frontend
| Kategorie | Technologien |
|-----------|--------------|
| **Framework** | React 19, TypeScript 5.7 |
| **Build-Tool** | Vite 6.2 |
| **Styling** | Tailwind CSS 4, Material-UI v6 |
| **Routing** | React Router DOM v7 |
| **HTTP-Client** | Axios 1.8 |
| **Animationen** | Framer Motion, GSAP |
| **Container** | Nginx (Multi-Stage-Build) |

### DevOps
| Kategorie | Technologien |
|-----------|--------------|
| **Container** | Docker, Docker Compose |
| **Reverse Proxy** | Nginx (600s Timeout für KI) |
| **Netzwerk** | Bridge-Netzwerk zwischen Services |

---

## Projektstruktur

```
Projekt/
├── Backend/
├── Frontend/
├── docker-compose.yml
├── .env
└── README.md

```


---

## KI-Kernfunktionen

### `nlp_utils.py` – NLP & OpenAI

| Funktion | Beschreibung |
|----------|--------------|
| `generate_test_cases()` | Generiert 5 Testfälle pro Anforderung via GPT |
| `kläre_anforderungen()` | Prüft auf Klärungsbedarf, generiert Rückfragen & Verbesserungsvorschläge |
| `multi_rag_suche_complet()` | Kombinierte Suche in RAG-Dateien + Datenbank |
| `classify_requirements()` | Klassifiziert Anforderungen (funktional/nicht-funktional) |
| `prioritize_test_cases()` | Priorisiert Testfälle (hoch/mittel/niedrig) via GPT |
| `generate_test_script()` | Generiert Testcode (pytest/selenium) via GPT |

### RAG-Suche (Semantische Ähnlichkeit)

```python
# Embedding mit SentenceTransformer
embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Kosinus-Ähnlichkeit für Kontextsuche
sim_scores = cosine_similarity(query_embedding, doc_embeddings)[0]

# Schwellenwerte: Dateien > 0.6, DB > 0.3
```

### Klärungslogik (Clarification-Flow)
Bei unvollständigen Anforderungen gibt das System zurück:
```json
{
    "needs_clarification": true,
    "questions": [
        "Wie soll der Benutzer seine Identität verifizieren?",
        "Soll eine E-Mail-Benachrichtigung gesendet werden?"
    ],
    "suggested_updates": "Das System soll das Passwort zurücksetzen, indem..."
}
```
## Voraussetzungen
- Docker & Docker Compose installiert
- OpenAI API Key (für KI-Funktionen)
- Node.js
- Python 3.10
- PostgreSQL ( via Docker)

## Installation & Start

### Docker Compose (Empfohlen)

``` bash
# 1. Repository klonen
git clone https://github.com/guita237/KI-Testcase.git
cd KI-Testcase

# 2. .env-Datei erstellen (siehe unten)
cp .env.example .env
# .env mit deinen Werten befüllen

# 3. Container starten
docker compose up --build

# 4. Anwendung aufrufen
# Frontend: http://localhost:8084
# Backend-API: http://localhost:5000
```
### lokale Entwicklung
#### Backend
```bash
cd Backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask db upgrade
flask run --port 5000
```
#### Frontend
```bash
cd Frontend
npm install
npm run dev
```

## Docker Compose (Empfohlen)

```yaml
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s

  flask-app:
    build: ./Backend
    environment:
      DATABASE_URL: ${DATABASE_URL}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      # ... weitere Variablen
    depends_on:
      db:
        condition: service_healthy
    command: sh -c "flask db upgrade && gunicorn -b 0.0.0.0:5000 --timeout 120 main:app"

  frontend:
    build: ./Frontend
    ports:
      - "8084:80"
    depends_on:
      - flask-app
```
## Umgebungskonfiguration
Erstelle eine .env-Datei im Projekt-Hauptverzeichnis:
```env
# ==================== DATENBANK ====================
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydatabase
DATABASE_URL=postgresql://myuser:mypassword@db:5432/mydatabase

# ==================== FLASK ====================
FLASK_SECRET_KEY=dein_geheimer_schluessel

# ==================== OPENAI ====================
OPENAI_API_KEY=sk-...

# ==================== FIREBASE ====================
FIREBASE_API_KEY=dein_firebase_api_key
FIREBASE_CREDENTIALS_PATH=./Firebase/serviceAccount.json

# ==================== E-MAIL (SMTP) ====================
SMTP_HOST=smtp.web.de
SMTP_PORT=587
SMTP_EMAIL=deine_email@example.com
SMTP_PASSWORD=dein_passwort
APP_NAME=KI-Testmanagement

# ==================== FRONTEND ====================
VITE_API_URL=http://localhost:5000
FRONTEND_URL=http://localhost:8084
```

## Forschungsfragen & Ergebnisse

### Frage 1: Zuverlässigkeit der KI-Testfallgenerierung

Die Evaluation zeigt, dass der Prototyp klar formulierte Anforderungen zuverlässig in formal korrekte, strukturierte Testfälle transformiert. Bei unklaren Anforderungen aktiviert das System die Rückfragenlogik.

**Ergebnis:** Hohe Zuverlässigkeit bei präzisen Anforderungen; Klärungslogik verbessert die Robustheit.

### Frage 2: Rolle von zusätzlichem Kontext (RAG)

Die Analyse der RAG-Komponente zeigt, dass zusätzlicher Kontext aus Dokumenten und Datenbanken einen signifikanten Einfluss auf die Qualität der generierten Testfälle hat.

**Ergebnis:** RAG führt zu erhöhter Präzision, inhaltlicher Tiefe und besserer Abdeckung komplexer Anforderungen.

---

## Fazit & Ausblick

### Fazit

Die Arbeit zeigt, dass die Kombination aus LLM, RAG und Rückfragenlogik eine effektive Grundlage für die automatisierte Testfallgenerierung darstellt. Der entwickelte Prototyp reduziert den manuellen Aufwand bei der Erstellung von Testfällen und erfüllt die grundlegenden Anforderungen an einen Testprozess.

### Ausblick

- Erweiterung der Wissensbasis durch zusätzliche Dokumente
- Performance-Optimierung durch Caching und effizientere Embedding-Modelle
- Automatische Priorisierung von Testfällen
- Generierung ausführbarer Testskripte (pytest, Selenium)
- Upload-Funktion für Anforderungsdokumente (PDF, DOCX, XLSX)