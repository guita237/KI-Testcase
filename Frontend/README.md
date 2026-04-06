# KI-gestütztes Testmanagement – Frontend (React + TypeScript)

Eine moderne React-Webanwendung für KI-gestütztes Testmanagement. Entwickelt mit **React 19**, **TypeScript**, **Vite**, **Material-UI (MUI)** und **Tailwind CSS**. Die App bietet eine benutzerfreundliche Oberfläche für Projektverwaltung, Testfallgenerierung mit KI-Unterstützung, Logging und Benutzerprofilverwaltung.

---

## 📋 Inhaltsverzeichnis

- [Technologien](#technologien)
- [Projektstruktur](#projektstruktur)
- [Hauptfunktionen](#hauptfunktionen)
- [Docker](#docker)
- [Konfiguration](#konfiguration)
- [Verwendung](#verwendung)
- [Screenshots](#screenshots)

---

## Technologien

| Kategorie | Technologien |
|-----------|--------------|
| **Framework** | React 19, TypeScript 5.7 |
| **Build-Tool** | Vite 6.2 |
| **Styling** | Tailwind CSS 4, Material-UI (MUI) v6, Emotion |
| **Routing** | React Router DOM v7 |
| **HTTP-Client** | Axios 1.8 |
| **Animationen** | Framer Motion 12.5, GSAP 3.12 |
| **Icons** | Lucide React, MUI Icons |
| **Benachrichtigungen** | React Toastify 11 |
| **Dateiverarbeitung** | Mammoth (DOCX), PDF.js, XLSX |
| **Container** | Docker + Nginx (Multi-Stage-Build) |

---

## Projektstruktur

```
Frontend/
├── src/
│ ├── api/
│ │ └── axiosInstance.ts # Axios-Instanz mit Interceptors (Auth-Token, 401-Handling)
│ ├── assets/ # Statische Assets (Bilder, Fonts)
│ ├── components/ # Wiederverwendbare Komponenten
│ │ └── Menu.tsx # Navigationsmenü (seitenübergreifend)
│ ├── context/
│ │ └── Authcontext.tsx # React Context für Authentifizierung (Login/Logout)
│ ├── pages/ # Seitenkomponenten
│ │ ├── Login.tsx # Login-Seite mit Passwort-Reset-Modal
│ │ ├── Register.tsx # Registrierung mit E-Mail-Verifikation
│ │ ├── Dashboard.tsx # Projektübersicht (CRUD-Operationen)
│ │ ├── Testcasepage.tsx # Testfallgenerierung & -verwaltung (KI)
│ │ ├── Profile.tsx # Benutzerprofil (E-Mail-Update, Konto löschen)
│ │ ├── LogsPage.tsx # Benutzeraktivitäts-Logs (mit GSAP-Animation)
│ │ └── KISuggestionsPage.tsx # KI-generierte Vorschläge anzeigen
│ ├── routes/
│ │ └── AppRouter.tsx # React Router Konfiguration
│ └── services/ # API-Service-Schicht
│ ├── authService.ts # Login, Register, Passwort-Reset, Profil
│ ├── projectService.ts # Projekt-CRUD
│ ├── test.case.service.ts # Testfall-CRUD, Requirements, Redundanzen
│ ├── aiService.ts # KI-Endpunkte (Generation, Priorisierung, Skripte)
│ ├── logs.service.ts # Benutzeraktivitäten abrufen
│ ├── kisuggestion.service.ts # KI-Vorschläge verwalten
│ └── apiErrorHandler.ts # Zentrale Fehlerbehandlung für API-Aufrufe
│
├── public/ # Öffentliche Assets (favicon, etc.)
├── dist/ # Build-Ausgabe (für Nginx)
├── Dockerfile # Multi-Stage-Build (Node → Nginx)
├── nginx.conf # Nginx-Konfiguration (Proxy zu Flask-Backend)
├── package.json # Abhängigkeiten & Skripte
├── vite.config.ts # Vite-Konfiguration (Proxy, Aliase, Tailwind)
├── tsconfig.json # TypeScript-Konfiguration
└── index.html # HTML-Einstiegspunkt
```


---

## Hauptfunktionen

### 🔐 Authentifizierung
- Login mit E-Mail/Passwort (JWT-Token in `localStorage`)
- Registrierung mit E-Mail-Verifikationslink
- Passwort-Reset-Funktionalität
- Automatisches Logout bei 401 (abgelaufener Token)

### 📁 Dashboard & Projektverwaltung
- Alle Benutzerprojekte anzeigen
- Neues Projekt erstellen (Name + Beschreibung)
- Projekt bearbeiten (Name, Beschreibung)
- Projekt löschen (mit Bestätigung)
- Klick auf Projekt → Weiterleitung zur Testfall-Seite

### 🧪 Testfallgenerierung (KI-integriert)
- Anforderungstext eingeben
- Auswahl zwischen **Classic** und **BDD (Gherkin)** Format
- KI-generierte Testfälle via OpenAI GPT
- **Clarification-Flow**: Wenn die KI mehr Informationen benötigt, werden spezifische Fragen gestellt und Verbesserungsvorschläge angezeigt
- Testfälle anzeigen mit Syntax-Highlighting (Feature/Scenario/Given/When/Then für BDD)
- Einzelnen Testfall kopieren oder löschen
- Alle Testfälle eines Projekts löschen
- Filterung nach Anforderungen (Dropdown aus extrahierten Requirements)

### 👤 Benutzerprofil
- Profildaten anzeigen (Name, E-Mail, Rolle, Mitglied seit)
- E-Mail-Adresse aktualisieren (mit Bestätigungslink)
- Konto komplett löschen (mit Bestätigungsdialog)

### 📜 Logs
- Benutzeraktivitäten anzeigen (Projekt erstellt/aktualisiert/gelöscht, etc.)
- **GSAP-Animation** beim Laden der Log-Liste (Stagger-Effekt)
- Icons basierend auf Aktionstyp (Create/Update/Delete)
- Formatierte Datumsanzeige

### 💡 KI-Vorschläge
- KI-generierte Optimierungsvorschläge anzeigen
- Vorschläge löschen (optional)

### 🧭 Navigation
- Seitenübergreifendes Navigationsmenü (`Menu.tsx`)
- Zurück-Button auf Detailseiten (`useNavigate(-1)`)

---

## API-Integration

Die `axiosInstance.ts` ist das zentrale Herzstück der API-Kommunikation:

```typescript
// Automatischer Token-Injection
axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) config.headers["Authorization"] = `Bearer ${token}`;
    return config;
});

// 401-Handling → automatisches Logout
axiosInstance.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            logoutUser(); // Token löschen, Benutzer abmelden
        }
        return Promise.reject(error);
    }
);
```

## Wichtige Service-Funktionen

| Service | Funktionen |
|---------|-------------|
| `authService` | `login()`, `registerUser()`, `resetPassword()`, `getUserProfile()`, `updateEmail()`, `deleteUser()` |
| `projectService` | `createProject()`, `getUserProjects()`, `updateProject()`, `deleteProject()` |
| `test.case.service` | `getTestCasesByProject()`, `getRequirementsByProject()`, `deleteTestCase()`, `getTestCasesByRequirement()` |
| `aiService` | `generateTestCases()`, `generateTestScript()`, `prioritizeTestCases()`, `classifyRequirements()`, `findRedundantTestCases()` |
| `logs.service` | `getLogsByUser()` |
| `kisuggestion.service` | `getKISuggestions()`, `deleteKISuggestion()` |

---

## Docker

### Multi-Stage-Build Dockerfile

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```
## Nginx-Konfiguration (nginx.conf)

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # React Router Support (SPA)
    location / {
        try_files $uri /index.html;
    }

    # Proxy zu Flask-Backend
    location /api/ {
        rewrite ^/api/?(.*)$ /$1 break;
        proxy_pass http://flask-app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Lange Timeouts für KI-Operationen (600s)
        proxy_connect_timeout 600;
        proxy_read_timeout 600;
        proxy_send_timeout 600;
    }
}
```
---
## Konfiguration

### Entwicklungsumgebung (vite.config.ts)
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
    plugins: [react(), tailwindcss()],
    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://localhost:5000', // Flask-Backend
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '/'),
            },
        },
    },
    resolve: {
        alias: { '@': path.resolve(__dirname, 'src') },
    },
});
``` 

## Verwendung

### Lokale Entwicklung

```bash
# Abhängigkeiten installieren
npm install

# Entwicklungsserver starten (http://localhost:5173)
npm run dev

# TypeScript-Check & Build
npm run build

# Vorschau des Builds
npm run preview

# Linting
npm run lint
```

### Mit Docker

```bash 
# Docker-Image bauen
docker build -t frontend-app .
# Container starten (stellt auf Port 80 bereit)
docker run -d -p 80:80  frontend-app
```
## Besonderheiten

### 🎨 Animationen
- **Framer Motion**: Seite-Übergänge und sanfte Einblendungen (Login, Register, Dashboard)
- **GSAP**: Logs-Seite mit gestaffelten Animationen (`stagger: 0.1`)

### 🔄 Clarification-Flow (KI)
Wenn die generierte Antwort `needs_clarification: true` enthält, zeigt die App:
- Spezifische Fragen zur Anforderung
- Einen verbesserten Vorschlag (suggested_updates)
- Button zum Übernehmen des Vorschlags

### 📱 Responsive Design
- Tailwind CSS Grid/Flex für mobile & Desktop
- Material-UI Komponenten mit eigenem Styling-Override

### 🔒 Sicherheit
- JWT-Token in `localStorage` (automatischer Header-Injection)
- Automatische Abmeldung bei 401 (abgelaufener/ungültiger Token)
- Geschützte Routen via `AuthContext`

---

