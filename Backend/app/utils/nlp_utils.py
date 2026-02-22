import openai
from openai import OpenAI, timeout, OpenAIError
import os
import re
from pathlib import Path
import json
import numpy as np
from typing import Dict, List, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.models import RAGReference

# OpenAI API-Schlüssel aus der .env-Datei laden
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


BASE_DIR = Path(__file__).resolve().parent.parent

RAG_CONFIG = {
    "Sicherheit": [
        str(BASE_DIR / "rag_docs/sicherheit/passwortrichtlinie.txt"),
        str(BASE_DIR / "rag_docs/sicherheit/2fa_policy.md")
    ],
    "UI": [
        str(BASE_DIR / "rag_docs/ui/login_standard.txt")
    ]
}



def generate_test_cases(requirements_text, model="gpt-4o-mini", temperature=0.5):
    """
    Generiert prägnante Testfälle aus Anforderungen im Streaming-Modus mit robustem Fehlerhandling.
    """
    try:
        # Streaming-Anfrage an das Modell
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Experte für Softwaretests und schreibst kurze, prägnante Testfälle basierend auf den gegebenen Anforderungen."
                },
                {
                    "role": "user",
                    "content": f"Erstelle 5 kurze und strukturierte Testfälle für jeden den folgenden Anforderungen:\n{requirements_text}\n"
                               f"Jeder Testfall sollte das Format haben: TC<Nummer> - [kurze Beschreibung]."
                }
            ],
            temperature=temperature,
            stream=True,  # Aktiviere Streaming
        )

        # Ergebnis zeilenweise empfangen und verarbeiten
        test_cases = []
        for chunk in stream:
            # Prüfen, ob der Chunk eine gültige 'delta'-Struktur hat
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                # Hinzufügen des Inhalts zur Testfallliste
                content = delta.content
                test_cases.append(content)
                print(content, end="")  # Debug-Ausgabe im Terminal

        # Kombiniere alle Teile der Antwort zu einem String
        return "".join(test_cases).strip()
    except Exception as e:
        return f"Fehler bei der Testfallgenerierung im Streaming-Modus: {str(e)}"


def kläre_anforderungen(anforderungstext: str, rag_context: Optional[str] = None) -> Dict:
    """
    Q&A-Modul mit optionalem Kontext und verbesserten Rückfragen.
    Gibt zurück: {"needs_clarification": bool, "questions": [], "suggested_updates": str}
    """
    system_prompt = f"""
Analysieren Sie die gegebene Anforderung und geben Sie ein JSON-Objekt zurück mit folgendem Schema:

{{
  "needs_clarification": true/false,
  "questions": [Liste präziser Nachfragen],
  "suggested_updates": "Vorgeschlagene, VERBESSERTE und detailliertere Version der Anforderung"
}}

Kontext für die Analyse (falls vorhanden):
{rag_context or 'Kein zusätzlicher Kontext'}

Wichtige Anweisungen:
1. stellen Sie nur Rückfragen, wenn ein vollständiger Test nicht möglich ist und keine plausible Annahme getroffen werden kann.
2. Falls der Kontext bereits Antworten liefert, **stellen Sie dazu keine Rückfragen mehr**.
3. Der vorgeschlagene Update-Text ("suggested_updates") soll versuchen, diese Fragen direkt zu beantworten, mit typischen, plausiblen Werten aus dem Kontext oder allgemein anerkannten Standards.
4. Der Update-Text MUSS in der gleichen Sprache wie die Eingabe formuliert sein.
5. Falls keine Verbesserung notwendig ist, wiederholen Sie den Originaltext.

Beispiel-Input:
"Das System soll Login-Fehlversuche behandeln"

Beispiel-Output:
{{
  "needs_clarification": true,
  "questions": [
    "Nach wie vielen Fehlversuchen soll das Konto gesperrt werden?",
    "Soll eine temporäre oder permanente Sperre erfolgen?"
  ],
  "suggested_updates": "Das System soll nach 3 fehlgeschlagenen Login-Versuchen den Benutzer für 30 Minuten sperren und eine E-Mail-Benachrichtigung senden."
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": anforderungstext}
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )

    return json.loads(response.choices[0].message.content)


def load_rag_files(rag_config: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Lädt RAG-Dokumente aus Dateien basierend auf der übergebenen Konfiguration.

    :param rag_config: Dictionary mit Kategorien als Schlüssel und einer Liste von Dateipfaden als Werte
    :return: Dictionary mit geladenen Dokumenten je Kategorie
    """
    loaded_docs = {}

    for kategorie, dateipfade in rag_config.items():
        docs = []
        for dateipfad in dateipfade:
            try:
                with open(dateipfad, 'r', encoding='utf-8') as f:
                    content = f.read()
                    docs.append(content)
                    print(f"[INFO] RAG-Datei erfolgreich geladen: {dateipfad} (Länge: {len(content)} Zeichen)")
            except Exception as e:
                print(f"[WARNUNG] Konnte RAG-Datei {dateipfad} nicht laden: {str(e)}")
                continue
        if docs:
            loaded_docs[kategorie] = docs
            print(f"[INFO] {len(docs)} Dokument(e) für Kategorie '{kategorie}' geladen.")
        else:
            print(f"[WARNUNG] Keine Dokumente für Kategorie '{kategorie}' geladen.")

    return loaded_docs


def multi_rag_suche_complet(query: str, dateibasierte_docs: Dict[str, List[str]], top_k: int = 2) -> str:
    """
    Kombiniert Dokumente aus Dateien + DB (RAGReference) und gibt den besten Kontext zurück.
    """
    kontext = ""

    # 1. Dateibasierte Suche (klassisch)
    if dateibasierte_docs:
        print(f"[INFO] Starte dateibasierte Suche für Query: '{query}'")
        for kategorie, docs in dateibasierte_docs.items():
            if not docs:
                print(f"[WARNUNG] Keine Dokumente in Kategorie '{kategorie}'")
                continue
            print(f"[INFO] Kategorie '{kategorie}': {len(docs)} Dokument(e) verfügbar")
            doc_embeddings = embedder.encode(docs)
            query_embedding = embedder.encode([query])
            sim_scores = cosine_similarity(query_embedding, doc_embeddings)[0]
            print(f"[DEBUG] Ähnlichkeitswerte (Dateien): {sim_scores}")

            if np.max(sim_scores) > 0.6:
                best_idx = np.argmax(sim_scores)
                print(f"[INFO] Beste Datei in Kategorie '{kategorie}' mit Score {sim_scores[best_idx]:.4f}")
                kontext += f"\n[{kategorie.upper()} KONTEXT]\n{docs[best_idx]}\n"
            else:
                print(f"[INFO] Keine Datei in Kategorie '{kategorie}' überschreitet den Schwellenwert")

    # 2. Datenbankbasierte Suche (RAGReference)
    rag_references = RAGReference.query.all()
    if rag_references:
        print(f"[INFO] Starte datenbankbasierte Suche mit {len(rag_references)} Einträgen")
        reference_texts = [r.test_case_text for r in rag_references]
        reference_embeddings = embedder.encode(reference_texts)
        query_embedding = embedder.encode([query])
        sim_scores = cosine_similarity(query_embedding, reference_embeddings)[0]
        print(f"[DEBUG] Ähnlichkeitswerte (DB): {sim_scores}")

        # Top-K ähnliche Testcases
        best_indices = np.argsort(sim_scores)[::-1][:top_k]
        for idx in best_indices:
            if sim_scores[idx] > 0.3:
                ref = rag_references[idx]
                print(f"[INFO] DB-Referenz ausgewählt (Index {idx}) mit Score {sim_scores[idx]:.4f}")
                kontext += f"\n[RAG-DB REF]\nAnforderung: {ref.requirement_text}\nTestfall: {ref.test_case_text}\n"
            else:
                print(f"[INFO] DB-Referenz (Index {idx}) hat Score {sim_scores[idx]:.4f}, unterhalb Schwellenwert")

    if not kontext:
        print("[INFO] Kein relevanter Kontext gefunden (Dateien + DB)")

    return kontext



def generiere_testfälle(
        anforderungstext: str,
        format: str = "bdd",
        rag_kategorien: Optional[Dict[str, List[str]]] = None,
        rag_config: Optional[Dict[str, List[str]]] = None,
        force: bool = False
) -> str:
    """
    Hauptfunktion mit strikten Formatvorgaben.
    """
    # 1. RAG-Kontext vorbereiten
    rag_context = ""
    if rag_config:
        loaded_docs = load_rag_files(rag_config)
        rag_context = multi_rag_suche_complet(anforderungstext, loaded_docs)
    elif rag_kategorien:
        rag_context = multi_rag_suche_complet(anforderungstext, rag_kategorien)

    # 2. Q&A-Klärung mit Kontext
    klärung = kläre_anforderungen(anforderungstext, rag_context)
    if klärung.get("needs_clarification") and not force:
        return json.dumps(klärung, ensure_ascii=False)
    elif klärung.get("needs_clarification") and force:
        print(" Unscharfe Anforderung, aber Zwangsgenerierung über `force=True`")

    # 3. Prompt vorbereiten
    system_prompt = f"""Generieren Sie Testfälle im geforderten Format:

=== STRENGE FORMATVORGABEN ===
{'BDD (Gherkin):' if format == 'bdd' else 'Klassisch:'}

{'''Feature: [Funktionsname]
  Scenario: [Szenarioname]
    Given [Vorbedingung]
    When [Aktion]
    Then [Erwartung]''' if format == 'bdd' else '''Name: TC[ID]: [Kurzbeschreibung]
Beschreibung: [Details]
Vorbedingungen: [Liste]
Testschritte:
  1. [Schritt 1]
  2. [Schritt 2]
Erwartetes Ergebnis:
  - [Erwartung 1]
  - [Erwartung 2]'''}

WICHTIG:
- Jede einzelne Anforderung muss vollständig abgedeckt werden
- Keine logischen Pfade auslassen
- Mindestens ein Testfall pro Kernanforderung
- Edge Cases nicht vergessen

Zusätzlicher Kontext:
{rag_context or 'Kein Zusatzkontext'}"""

    user_prompt = f"""Anforderungen:
{anforderungstext}

Generieren Sie für ALLE Anforderungen vollständige Testfälle im {'BDD' if format == 'bdd' else 'klassischen'} Format.
Stellen Sie sicher, dass:
1. Jede Anforderung mindestens einen Testfall hat
2. Alle logischen Pfade abgedeckt sind
3. Die vorgegebene Struktur exakt eingehalten wird"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            timeout=120  # Timeout für lange Antworten
        )
        return validiere_ausgabe(response.choices[0].message.content, format)

    except openai.APIConnectionError as e:
        print(f"Verbindungsfehler zu OpenAI: {e}")
        return json.dumps({"error": "Verbindungsfehler zu OpenAI"}, ensure_ascii=False)

    except openai.APITimeoutError as e:
        print(f"Timeout beim Warten auf OpenAI-Antwort: {e}")
        return json.dumps({"error": "Timeout bei OpenAI"}, ensure_ascii=False)

    except OpenAIError as e:
        print(f"OpenAI API-Fehler: {e}")
        return json.dumps({"error": f"OpenAI-Fehler: {str(e)}"}, ensure_ascii=False)

def validiere_ausgabe(roh_output: str, format: str) -> str:
    """Erzwingt exakte Formatierung"""
    if format == "bdd":
        if not re.search(r"Feature:\s*.+\n\s*Scenario:\s*.+", roh_output):
            return "FEHLER: Ungültiges BDD-Format. Beispiel:\nFeature: Login\n  Scenario: Erfolgreiche Anmeldung\n    Given [...]"
        return roh_output
    else:
        if not re.search(r"Name:\s*TC\d+:.*\nBeschreibung:", roh_output):
            return "FEHLER: Ungültiges klassisches Format. Beispiel:\nName: TC1: Testfall\nBeschreibung: [...]\nTestschritte:\n  1. [...]"
        return roh_output

def parse_test_cases(raw_text: str, format: str = "classic") -> List[Dict]:
    """
    Analyse la réponse brute selon le format spécifié.
    Retourne une liste de dictionnaires {name, full_description}
    """
    test_cases = []

    if format == "bdd":
        current_feature = ""
        for line in raw_text.split("\n"):
            line = line.strip()
            if line.startswith("Feature:"):
                current_feature = line[8:].strip()
            elif line.startswith("Scenario:"):
                scenario = line[9:].strip()
                test_cases.append({
                    "name": f"{current_feature} - {scenario}",
                    "full_description": raw_text  # Stocke tout le feature/scenario
                })
    else:
        current_case = None
        buffer = []

        for line in raw_text.split("\n"):
            line = line.strip()
            if line.startswith("Name: TC"):
                if current_case:
                    current_case["full_description"] = "\n".join(buffer)
                    test_cases.append(current_case)
                current_case = {
                    "name": line[5:].strip(),  # Enlève "Name:"
                    "full_description": ""
                }
                buffer = [line]
            elif current_case:
                buffer.append(line)

        if current_case:
            current_case["full_description"] = "\n".join(buffer)
            test_cases.append(current_case)

    return test_cases

# Beispielaufruf
if __name__ == "__main__":
    # Konfiguration der RAG-Dateien
    RAG_CONFIG = {
        "Sicherheit": [
            "rag_docs/sicherheit/passwortrichtlinie.txt",
            "rag_docs/sicherheit/2fa_policy.md"
        ],
        "UI": [
            "rag_docs/ui/login_standard.txt"
        ]
    }

    # BDD-Beispiel mit RAG
    print("=== BDD mit RAG ===")
    print(generiere_testfälle(
        "Benutzer-Login mit Email/Passwort",
        format="bdd",
        rag_config=RAG_CONFIG
    ))

    # Klassisches Beispiel ohne RAG
    print("\n=== Klassisch ohne RAG ===")
    print(generiere_testfälle(
        "Passwort-Reset per Email",
        format="classic"
    ))

# Funktion: GPT-gestützte Extraktion von Anforderungen
def generate_summary(text, model="gpt-4o-mini", temperature=0.3):
    """
    Extrahiert eine Liste von Anforderungen aus dem gegebenen Text.

    :param text: Der Eingabetext, aus dem die Anforderungen extrahiert werden sollen.
    :param model: Das GPT-Modell, das verwendet werden soll (z. B. "gpt-4o-mini").
    :param temperature: Steuerung der Kreativität der Antwort.
    :return: Liste von Anforderungen als Text.
    """
    try:
        # Streaming-Anfrage an das Modell
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du bist ein erfahrener Business-Analyst. "
                        "Extrahiere alle Anforderungen aus einem gegebenen Text "
                        "und gib sie als einfache Liste zurück. "
                        "Die Anforderungen sollten klar, prägnant und ohne unnötige Details formuliert sein. "
                        "Gib nur die Anforderungen zurück – keine Einleitung, keine Erklärungen, keine Formatierung."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Extrahiere die Anforderungen aus folgendem Text:\n{text}\n\n"
                        "Format:\n"
                        "- Anforderung 1\n"
                        "- Anforderung 2\n"
                        "- Anforderung 3\n"
                        "\nGib NUR die Liste der Anforderungen zurück, ohne weitere Kommentare oder Formatierungen."
                    )
                }
            ],
            temperature=temperature,
            stream=True,  # Aktiviert Streaming für bessere Performance
        )

        # Ergebnis zeilenweise empfangen und verarbeiten
        requirements = []
        for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                content = delta.content
                requirements.append(content)
                print(content, end="")  # Debug-Ausgabe im Terminal

        # Kombiniere alle Teile der Antwort zu einer sauberen Liste
        return "\n".join(requirements).strip()

    except Exception as e:
        return f"Fehler bei der Extraktion der Anforderungen: {str(e)}"



# Funktion: GPT-gestützte Klassifikation von Anforderungen
def classify_requirements(text, model="gpt-4o-mini", temperature=0.3):
    """
    Klassifiziert Anforderungen in verschiedene Kategorien wie funktional, nicht-funktional, Regression, Integration, Unit-Test etc.

    :param text: Die Anforderung als Text.
    :param model: Das GPT-Modell, das verwendet werden soll (z. B. "gpt-4").
    :param temperature: Steuerung der Kreativität der Antwort.
    :return: Klassifikationsergebnis als strukturierter Text.
    """

    try:
        #  Optimierter Prompt für präzisere Klassifikation
        prompt = (
            "Du bist ein erfahrener Softwaretester. Deine Aufgabe ist es, Anforderungen basierend auf ihrem Typ zu klassifizieren.\n"
            "\n  **Regeln für die Klassifikation:**"
            "\n- Antworte nur mit der Kategorie, ohne zusätzliche Erklärung."
            "\n- Jede Anforderung gehört zu einer der folgenden Kategorien:"
            "\n  - **funktional**: Beschreibt eine konkrete Funktion der Software."
            "\n  - **nicht-funktional**: Beschreibt Qualitätsmerkmale wie Performance, Sicherheit, Benutzerfreundlichkeit."
            "\n  - **regression**: Testet, ob bestehende Funktionen nach einer Änderung weiterhin funktionieren."
            "\n  - **integration**: Überprüft die Interaktion zwischen verschiedenen Modulen oder Systemen."
            "\n  - **unit-test**: Testet einzelne Komponenten oder Funktionen isoliert."
            "\n  - **system-test**: Testet das gesamte System als Ganzes."
            "\n  - **akzeptanztest**: Prüft, ob das System die Anforderungen des Endbenutzers erfüllt."
            "\n  - **lasttest**: Bewertet die Leistung unter hoher Last."
            "\n  - **sicherheitstest**: Bewertet die Sicherheitsmechanismen der Anwendung."
            "\n\n **Hier ist die zu klassifizierende Anforderung:**"
            f"\n{text}"
        )

        #  Anfrage an das GPT-Modell
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein KI-Experte für Softwaretest-Klassifikation."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=50  # Begrenzung auf kurze und präzise Antwort
        )

        #  Antwort extrahieren und bereinigen
        return response.choices[0].message.content.strip().lower()

    except Exception as e:
        return f"Fehler bei der Klassifikation: {str(e)}"

# Funktion: Klassifizierung mehrerer Anforderungen auf einmal
def classify_multiple_requirements(requirements_list, model="gpt-4o-mini", temperature=0.3):
    """
    Klassifiziert eine Liste von Anforderungen in verschiedene Testkategorien.
    Arbeitet im Streaming-Modus für effiziente Verarbeitung.

    :param requirements_list: Liste von Anforderungen (Strings).
    :param model: GPT-Modell für die Klassifizierung.
    :param temperature: Steuerung der Antwortvielfalt.
    :return: Liste von Klassifikationen.
    """
    try:
        #  Prompt vorbereiten
        prompt = (
            "Du bist ein erfahrener Softwaretester und klassifizierst Anforderungen in verschiedene Testkategorien:\n"
            "- **funktional** (Functional Test)\n"
            "- **nicht-funktional** (Non-Functional Test)\n"
            "- **regression** (Regression Test)\n"
            "- **integration** (Integration Test)\n"
            "- **unit-test** (Unit Test)\n"
            "- **system-test** (System Test)\n"
            "- **akzeptanztest** (User Acceptance Test, UAT)\n"
            "- **lasttest** (Performance oder Last Test)\n"
            "- **sicherheitstest** (Security Test)\n"
            "\n"
            "Gib NUR die Kategorie für jede Anforderung zurück, ohne zusätzliche Erklärungen.\n"
            "\n"
            "Hier sind die Anforderungen:\n"
        )
        prompt += "\n".join([f"{i+1}. {req}" for i, req in enumerate(requirements_list)])

        #  GPT API-Aufruf (Streaming-Modus)
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein KI-Experte für Softwaretests."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            stream=True,  # Streaming aktiviert
        )

        #  Antwort verarbeiten
        classifications = []
        collected_text = ""

        for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                collected_text += delta.content
                print(delta.content, end="")  # Debugging

        #  Ergebnisse in eine Liste umwandeln
        classification_list = collected_text.strip().split("\n")
        classifications = [cls.strip().lower() for cls in classification_list]

        return classifications

    except Exception as e:
        return [f"Fehler: {str(e)}"] * len(requirements_list)




# Funktion: GPT-gestützte Priorisierung von Testfällen
def prioritize_test_cases(test_cases, model="gpt-4o-mini", temperature=0.3):
    """
    Priorisiert eine Liste von Testfällen basierend auf Risiko, Komplexität und Auswirkungen.
    Korrigierte Version mit verbesserter Extraktion der Prioritäten.
    """

    try:
        # Optimierter Prompt für die KI
        prompt = (
            "Du bist ein erfahrener Softwaretester und priorisierst Testfälle basierend auf Risiko, "
            "Komplexität und Auswirkungen. Weise jedem Testfall eine eindeutige Priorität zu.\n\n"
            " **Wichtige Anweisungen für die Antwort:**\n"
            "- Keine Einleitung oder Erklärung, direkt mit der Liste beginnen.\n"
            "- Jede Zeile sollte genau einen Testfall enthalten.\n"
            "- Format: **Nummer. Testfall - Priorität (hoch, mittel, niedrig)**\n\n"
            " **Hier sind die Testfälle:**\n"
        )

        prompt += "\n".join([f"{i + 1}. {tc}" for i, tc in enumerate(test_cases)])

        #  Debugging : Afficher le prompt envoyé
        print(" Senden des Prompts an die KI:\n", prompt)

        # Streaming-Anfrage an das Modell
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein KI-Experte für Softwaretests."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            stream=True,  # Streaming aktivieren
        )

        #  Antwort verarbeiten
        collected_text = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                collected_text += delta.content
                print(delta.content, end="")  # Debugging-Ausgabe

        #  Falls die Antwort leer ist, Debugging ausgeben
        if not collected_text.strip():
            print(" Die KI hat eine leere Antwort gesendet.")
            return []

        print("\n KI-Rohantwort vollständig empfangen:\n", collected_text)

        #  Zeilenweise verarbeiten und Prioritäten extrahieren
        lines = collected_text.strip().split("\n")
        priority_mapping = []

        #  Regulärer Ausdruck für die Priorität
        priority_regex = re.compile(r" - Priorität \((hoch|mittel|niedrig)\)", re.IGNORECASE)

        for line in lines:
            match = priority_regex.search(line)
            if match:
                priority = match.group(1).lower()
                test_case = re.sub(r"^\d+\.\s+", "", line)  # Entferne die Nummerierung
                test_case = priority_regex.sub("", test_case).strip()  # Entferne die "Priorität (xyz)"

                priority_mapping.append({"test_case": test_case, "priority": priority})

        return priority_mapping

    except Exception as e:
        print(" Fehler bei der Priorisierung:", str(e))
        return []



# Funktion: Generierung von Testcode aus Testfällen
def generate_test_script(test_case_description, framework="pytest", model="gpt-4o-mini", temperature=0.5):
    """
    Erstellt automatisierten Testcode basierend auf einem Testfall und dem ausgewählten Framework im Streaming-Modus.

    :param test_case_description: Beschreibung des Testfalls.
    :param framework: Framework (z. B. 'pytest', 'selenium').
    :param model: GPT-Modell (z. B. 'gpt-4').
    :param temperature: Steuerung der Kreativität der Antwort.
    :return: Generierter Testcode als Text.
    """
    try:
        #  KI-Prompt mit strikter Anweisung zum Vermeiden von Einleitungen
        prompt = (
            f"Schreibe einen automatisierten Test für folgendes Test-Szenario mit {framework}.\n"
            f" **Wichtige Anweisungen:**\n"
            f"- Direkt den Code generieren, ohne Einleitung oder Erklärungaber, aber mit Kommentare.\n"
            f"- Der Testcode sollte vollständig lauffähig sein.\n"
            f"- Falls nötig, importiere alle erforderlichen Module.\n\n"
            f" **Testfall-Beschreibung:**\n{test_case_description}\n\n"
            f" **Gib nur den Code zurück:**"
        )

        #  Streaming-Anfrage an das Modell
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"Du bist ein Experte für Testautomatisierung mit {framework}."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            stream=True,  # Aktiviert Streaming für schnellere Verarbeitung
        )

        # KI-Antwort zeilenweise empfangen & verarbeiten
        script_code = []
        for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                script_code.append(delta.content)

        #  Testcode als String zurückgeben
        return "".join(script_code).strip()

    except Exception as e:
        return f"Fehler bei der Generierung des Testcodes im Streaming-Modus: {str(e)}"


# Funktion: Identifizierung redundanter Testfälle
def find_redundant_test_cases(test_cases, model="gpt-4o-mini", temperature=0.3):
    """
    Identifiziert redundante Testfälle basierend auf inhaltlicher Ähnlichkeit und Testabdeckung.
    Arbeitet im Streaming-Modus für eine effizientere Verarbeitung.

    :param test_cases: Liste von Testfallbeschreibungen.
    :param model: Das GPT-Modell, das verwendet werden soll (z. B. "gpt-4").
    :param temperature: Steuerung der Kreativität der Antwort.
    :return: Liste redundanter Testfälle als JSON-Objekt.
    """
    try:
        if not test_cases or len(test_cases) < 2:
            return {"error": "Zu wenige Testfälle für eine Redundanzprüfung."}

        #  Verbessertes Prompt für genauere KI-Erkennung
        prompt = (
            " Finde redundante Testfälle in der folgenden Liste:\n"
            "- Ein Testfall ist redundant, wenn er eine ähnliche oder identische Funktionalität testet.\n"
            "- Gib für jeden redundanten Testfall den originalen Testfall an, auf den er sich bezieht.\n"
            "- Format: [Redundanter Testfall] -> [Original Testfall]\n\n"
        )
        prompt += "\n".join([f"{i + 1}. {tc}" for i, tc in enumerate(test_cases)])

        #  KI-Anfrage im Streaming-Modus
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist ein erfahrener Softwaretester und erkennst redundante Testfälle."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            stream=True,
        )

        #  KI-Antwort zeilenweise sammeln
        collected_text = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                collected_text += delta.content
                print(delta.content, end="")  # Debugging-Ausgabe im Terminal

        #  Verarbeitung der KI-Antwort
        redundant_cases = []
        for line in collected_text.strip().split("\n"):
            if " -> " in line:
                parts = line.split(" -> ")
                if len(parts) == 2:
                    redundant_cases.append({
                        "redundant_test_case": parts[0].strip(),
                        "original_test_case": parts[1].strip()
                    })

        return {
            "message": "Redundante Testfälle erfolgreich identifiziert.",
            "redundant_test_cases": redundant_cases
        }

    except Exception as e:
        return {"error": f"Fehler bei der Erkennung redundanter Testfälle: {str(e)}"}
