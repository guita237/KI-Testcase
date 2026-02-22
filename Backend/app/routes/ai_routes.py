from flask import Blueprint, request, jsonify, send_file, send_from_directory
from app import db
from app.models import Project, TestCase, KISuggestion, Log, CodeChange, User, RAGReference
from app.utils import verify_token
from app.utils.nlp_utils import generate_test_cases, generate_summary, generate_test_script, \
    classify_requirements, prioritize_test_cases, find_redundant_test_cases, classify_multiple_requirements, \
    parse_test_cases, generiere_testfälle, load_rag_files
from  app.utils.datei_typ import extract_text_from_pdf , extract_text_from_xlsx, extract_text_from_docx
import difflib
import os
import re
import PyPDF2
import docx
import pandas as pd
import tempfile
from werkzeug.utils import secure_filename
import json
from pathlib import Path

ai_bp = Blueprint("ai_routes", __name__)

# Verzeichnis für gespeicherte Testskripte
SCRIPTS_FOLDER = "generated_scripts/"
os.makedirs(SCRIPTS_FOLDER, exist_ok=True)

#  Unterstützte Dateiformate für den Upload
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "xlsx"}


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

def allowed_file(filename):
    """ Überprüft, ob die Datei eine erlaubte Endung hat. """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Route: Testfälle generieren
@ai_bp.route("/generate-test-case", methods=["POST"])
def generate_test_cases_routes():
    """
    Diese Route generiert Testfälle für ein Projekt basierend auf den Anforderungen.
    Unterstützt Text- oder Datei-Upload (PDF, DOCX, XLSX, TXT)
    Verwendet `generate_summary()`, um Anforderungen zu extrahieren
    Speichert die generierten Testfälle in der Datenbank
    """

    # Authentifizierung überprüfen
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    created_by = decoded_token.get("uid")
    if not created_by:
        return jsonify({"error": "Benutzer-ID konnte nicht ermittelt werden"}), 403

    # Anfrage-Daten abrufen (falls Datei hochgeladen wurde, nutze `request.form`)
    data = request.form if "requirement_file" in request.files else request.get_json()
    project_id = data.get("project_id")

    if not project_id:
        return jsonify({"error": "Projekt-ID ist erforderlich"}), 400

    raw_requirements = None

    # Falls eine Datei hochgeladen wurde, Text extrahieren
    if "requirement_file" in request.files:
        file = request.files["requirement_file"]

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join("/tmp", filename)
            file.save(file_path)

            try:
                raw_text = extract_text_from_file(file_path)  # ✅ Dateiinhalt extrahieren
                raw_requirements = generate_summary(raw_text)  # ✅ Anforderungen mit KI extrahieren
            except Exception as e:
                return jsonify({"error": f"Fehler beim Einlesen der Datei: {str(e)}"}), 500
            finally:
                os.remove(file_path)  # 🔹 Temporäre Datei löschen

    # Falls kein Datei-Upload vorhanden ist, Anforderungen als Text übernehmen
    raw_requirements = data.get("requirements_text", "")

    # Überprüfen, ob `raw_requirements` eine Liste ist, und sie in eine Zeichenkette umwandeln
    if isinstance(raw_requirements, list):
        raw_requirements = "\n".join(raw_requirements)  # Liste zu einem String zusammenfügen

    raw_requirements = raw_requirements.strip()  # `.strip()` nur auf eine Zeichenkette anwenden

    if not raw_requirements:
        return jsonify({"error": "Keine Anforderungen gefunden"}), 400

    #  Extrahierte Anforderungen aufbereiten
    extracted_requirements = [req.strip("- ") for req in raw_requirements.split("\n") if req.strip()]

    if not extracted_requirements:
        return jsonify({"error": "Keine Anforderungen extrahiert"}), 400


    format_type = "classic"  # Par défaut
    if "format" in request.form or (request.is_json and "format" in request.get_json()):
        format_type = request.form.get("format") if "format" in request.form else request.get_json().get("format")

    # Generierung von Testfällen mit KI
    all_test_cases = []
    try:
        for req in extracted_requirements:
            raw_response = generate_test_cases(req)  # ✅ Aufruf zur Testfallgenerierung
            test_cases = extract_test_cases(raw_response)  # ✅ KI-Response analysieren

            if not test_cases:
                continue

            saved_test_cases = []
            for tc in test_cases:
                test_case_entry = TestCase(
                    name=tc["name"],
                    description=tc["description"].strip(),
                    project_id=project_id,
                    created_by=created_by,
                    requirement_text=req
                )
                db.session.add(test_case_entry)
                saved_test_cases.append(test_case_entry)

            all_test_cases.extend(saved_test_cases)

        db.session.commit()

        if not all_test_cases:
            return jsonify({"error": "Keine Testfälle generiert"}), 500

        return jsonify({
            "message": "Testfälle erfolgreich generiert und gespeichert",
            "test_cases": [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "description": tc.description,
                    "requirement_text": tc.requirement_text
                }
                for tc in all_test_cases
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": f"Fehler bei der Testfallgenerierung: {str(e)}"}), 500



#  Funktion zur Text-Extraktion aus Dateien
def extract_text_from_file(file_path):
    """
    Extrahiert Text aus PDF, DOCX, XLSX, TXT.
    :param file_path: Pfad zur Datei.
    :return: Extrahierter Text.
    """
    file_extension = file_path.rsplit(".", 1)[1].lower()

    if file_extension == "pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

    elif file_extension == "docx":
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    elif file_extension == "xlsx":
        df = pd.read_excel(file_path)
        return "\n".join(df.astype(str).stack().tolist())

    elif file_extension == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError("Nicht unterstütztes Dateiformat")


def extract_test_cases(response_text):
    """
    Extrahiert Testfälle aus einer KI-generierten Antwort.

    Unterstützte Formate:
    1. **TC1 - Kurze Beschreibung**
    2. *Ziel:* ... *Schritte:* ... *Erwartetes Ergebnis:*
    3. ### TC1 - [Testfallname]

    :param response_text: Die Antwort der KI als String.
    :return: Liste von Testfällen [{name, description}]
    """
    test_cases = []
    current_test_case = None
    description_accumulator = []

    for line in response_text.split("\n"):
        line = line.strip()

        #  Erkennen von Testfall-Titeln (verschiedene Formate)
        if re.match(r"(\*\*TC\d+|\- TC\d+|TC\d+|### TC\d+)", line):
            if current_test_case:
                current_test_case["description"] = " ".join(description_accumulator).strip()
                test_cases.append(current_test_case)  # Speichere den vorherigen Testfall

            current_test_case = {
                "name": line.strip("*#- "),  # Bereinigt Sonderzeichen
                "description": ""
            }
            description_accumulator = []

        elif current_test_case:
            #  Ziel-Abschnitt erkennen
            if line.startswith("*Ziel:*"):
                description_accumulator.append(line)

            #  Schritte-Abschnitt erkennen
            elif line.startswith("*Schritte:*"):
                description_accumulator.append(line)

            #  Erwartetes Ergebnis extrahieren
            elif line.startswith("*Erwartetes Ergebnis:*"):
                current_test_case["expected_result"] = line.replace("*Erwartetes Ergebnis:*", "").strip()

            else:
                description_accumulator.append(line)

    # Letzten Testfall speichern
    if current_test_case:
        current_test_case["description"] = " ".join(description_accumulator).strip()
        test_cases.append(current_test_case)

    return test_cases



@ai_bp.route("/generate-test-cases", methods=["POST"])
def generate_test_cases_route():
    """
    Endpoint für Testfallgenerierung mit RAG-Unterstützung
    Erwartet:
    - Header: Authorization: Bearer <JWT>
    - Body: {
        "project_id": int,
        "requirements_text": str (optional),
        "requirement_file": file (optional),
        "format": "bdd"|"classic" (default: "bdd")
    }
    """
    # 1. Authentifizierung
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    created_by = decoded_token.get("uid")
    if not created_by:
        return jsonify({"error": "Benutzer-ID konnte nicht ermittelt werden"}), 403




    # 2. Datenvalidierung
    data = request.form if "requirement_file" in request.files else request.get_json()
    project_id = data.get("project_id")
    format_type = data.get("format", "bdd")
    force_mode = data.get("force", False)


    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400

    # 3. Anforderungen extrahieren (Text oder Datei)
    raw_requirements = ""
    if "requirement_file" in request.files:
        file = request.files["requirement_file"]
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join("/tmp", filename)
                file.save(file_path)
                raw_text = extract_text_from_file(file_path)
                raw_requirements = generate_summary(raw_text)
                os.remove(file_path)
            except Exception as e:
                return jsonify({"error": f"File processing error: {str(e)}"}), 500
    else:
        raw_requirements = data.get("requirements_text", "")

    # 4. Anforderungen aufbereiten
    requirements = "\n".join(
        req.strip("- ") for req in raw_requirements.split("\n")
        if req.strip()
    )
    if not requirements:
        return jsonify({"error": "No requirements provided"}), 400


   # 6. Testfälle generieren
    try:
        # Generiere Rohantwort mit RAG-Kontext
        raw_response = generiere_testfälle(
            anforderungstext=requirements,
            format=format_type,
            rag_config=RAG_CONFIG,
            force=force_mode
        )
        try:
            maybe_clarification = json.loads(raw_response)
            if isinstance(maybe_clarification, dict) and maybe_clarification.get("needs_clarification"):
                return jsonify({
                    "success": False,
                    "message": "Requirement needs clarification",
                    "test_cases": [],
                    "clarification": maybe_clarification,
                    "warnings": []
                }), 202
        except Exception:
             pass

        # Parse die Antwort in Testfall-Objekte
        test_cases = parse_test_cases(raw_response, format_type)

        # In Datenbank speichern
        saved_cases = []
        for tc in test_cases:
            new_case = TestCase(
                name=tc["name"],
                description=tc["full_description"],
                project_id=project_id,
                created_by=created_by,
                requirement_text=requirements[:500]  # Erste 500 Zeichen
            )
            db.session.add(new_case)
            saved_cases.append(new_case)


        for tc in saved_cases:
           rag_ref = RAGReference(
              requirement_text=requirements,
              test_case_text=tc.description,
              category=None
           )
           db.session.add(rag_ref)


        db.session.commit()



        # Response formatieren
        return jsonify({
            "success": True,
            "message": f"Successfully generated {len(saved_cases)} test cases",
            "test_cases": [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "description": tc.description,
                    "requirement_text": tc.requirement_text
                }
                for tc in saved_cases
            ],
            "clarification": None,
            "warnings": []
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Test generation failed.",
            "test_cases": [],
            "clarification": None,
            "warnings": [],
            "error": str(e)
        }), 500

#  Route: Anforderungen extrahieren
@ai_bp.route("/extract-requirements", methods=["POST"])
def extract_requirements_route():
    """
    Extrahiert Anforderungen aus einem gegebenen Text oder einer hochgeladenen Datei.
    Unterstützt: TXT, PDF, DOCX, XLSX
    """
    #  Token-Authentifizierung prüfen
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    try:
        extracted_text = None

        #  Falls eine Datei hochgeladen wurde
        if "requirement_file" in request.files:
            file = request.files["requirement_file"]
            filename = secure_filename(file.filename)

            # Temporäre Datei speichern
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, filename)
            file.save(file_path)

            #  Dateityp erkennen und richtigen Parser verwenden
            if filename.endswith(".pdf"):
                extracted_text = extract_text_from_pdf(file_path)
            elif filename.endswith(".docx"):
                extracted_text = extract_text_from_docx(file_path)
            elif filename.endswith(".xlsx"):
                extracted_text = extract_text_from_xlsx(file_path)
            elif filename.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    extracted_text = f.read()
            else:
                return jsonify({"error": "Ungültiges Dateiformat. Erlaubt: TXT, PDF, DOCX, XLSX"}), 400

            os.remove(file_path)  # Temporäre Datei löschen

        #  Falls der Text direkt übergeben wurde
        else:
            data = request.get_json()
            extracted_text = data.get("requirements_text", "").strip()

        #  Validierung
        if not extracted_text:
            return jsonify({"error": "Kein gültiger Text oder Dateiinhalt gefunden."}), 400

        #  Anforderungen mit GPT extrahieren
        extracted_requirements = generate_summary(extracted_text)

        return jsonify({
            "message": "Anforderungen erfolgreich extrahiert.",
            "requirements": extracted_requirements.split("\n")  # In Liste umwandeln
        }), 200

    except Exception as e:
        return jsonify({"error": f"Fehler bei der Anforderungs-Extraktion: {str(e)}"}), 500


@ai_bp.route("/generate-test-script", methods=["POST"])
def generate_test_script_route():
    """
    Generiert automatisierte Testskripte für alle Testfälle mit demselben `requirement_text`.
    Speichert die Skripte in einer einzigen Datei und aktualisiert die Datenbank.
    """

    #  Token aus Header extrahieren & verifizieren
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    #  Benutzer-ID aus Token extrahieren
    created_by = decoded_token.get("uid")
    if not created_by:
        return jsonify({"error": "Benutzer-ID konnte nicht ermittelt werden"}), 403

    #  Daten aus Anfrage abrufen
    data = request.get_json()
    project_id = data.get("project_id")
    requirement_text = data.get("requirement_text")
    framework = data.get("framework", "pytest")

    if not requirement_text or not project_id:
        return jsonify({"error": "Projekt-ID und requirement_text sind erforderlich"}), 400

    try:
        #  Projekt abrufen und Berechtigung prüfen
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404

        if project.created_by != created_by:
            return jsonify({"error": "Keine Berechtigung für dieses Projekt"}), 403

        #  Alle Testfälle mit demselben `requirement_text` abrufen
        test_cases = TestCase.query.filter_by(project_id=project_id, requirement_text=requirement_text).all()
        if not test_cases:
            return jsonify({"error": "Keine Testfälle für diese Anforderung gefunden"}), 404

        #  Generierung des Testskripts für alle Testfälle
        combined_script = ""
        test_case_scripts = {}

        for test_case in test_cases:
            script_code = generate_test_script(test_case.description, framework=framework)
            test_case.test_script = script_code  # Skript in der DB speichern
            test_case_scripts[test_case.id] = script_code
            combined_script += f"# Testfall: {test_case.name}\n{script_code}\n\n"

        #  Datei mit generierten Skripten speichern
        filename = secure_filename(f"test_cases_project_{project_id}_{requirement_text[:20]}.py")
        script_path = os.path.join(SCRIPTS_FOLDER, filename)

        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.write(combined_script)

        #  DB aktualisieren
        for test_case in test_cases:
            existing_test_case = TestCase.query.get(test_case.id)
            if existing_test_case:
                existing_test_case.test_script = test_case_scripts[test_case.id]
                db.session.add(existing_test_case)

        #  Code-Änderung speichern
        code_change = CodeChange(
            file_name=filename,
            lines_changed=len(combined_script.split("\n")),
            commit_id="N/A",
            description=f"Testskripte für {len(test_cases)} Testfälle mit requirement_text gespeichert."
        )
        db.session.add(code_change)

        #  Log-Eintrag speichern
        log_entry = Log(
            user_id=created_by,
            action="Testskript generiert",
            description=f"Testskripte für {len(test_cases)} Testfälle gespeichert."
        )
        db.session.add(log_entry)

        #  KI-Vorschläge speichern
        for test_case_id in test_case_scripts.keys():
            ki_suggestion = KISuggestion(
                test_case_id=test_case_id,
                suggestion_type="generation",
                description="Automatisierter Testcode wurde generiert."
            )
            db.session.add(ki_suggestion)

        db.session.commit()

        return jsonify({
            "message": "Testskripte erfolgreich generiert",
            "download_url": f"/download/{filename}",  # 🔥 URL für den Download
            "test_cases": [
                {"id": tc.id, "name": tc.name, "script": test_case_scripts[tc.id]}
                for tc in test_cases
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Datei herunterladen
@ai_bp.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """
    Ermöglicht den Download einer generierten Testdatei.
    """
    return send_from_directory(SCRIPTS_FOLDER, filename, as_attachment=True)

# Route: Testcode herunterladen
@ai_bp.route("/download-test-script/<int:test_case_id>", methods=["GET"])
def download_test_script(test_case_id):
    script_path = os.path.join(SCRIPTS_FOLDER, f"test_case_{test_case_id}.py")
    if not os.path.exists(script_path):
        return jsonify({"error": "Testskript nicht gefunden"}), 404

    return send_file(script_path, as_attachment=True)

# Route: Testfälle priorisieren
@ai_bp.route("/prioritize-test-cases", methods=["POST"])
def prioritize_test_cases_route():
    """
    Priorisiert Testfälle für eine bestimmte Anforderung.
    Stellt sicher, dass die KI-Antworten korrekt mit den Datenbank-Testfällen verknüpft werden.
    """
    #  Authentifizierung prüfen
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    try:
        #  Anfrage-Daten abrufen
        data = request.get_json()
        project_id = data.get("project_id")
        requirement_text = data.get("requirement_text")

        if not project_id or not requirement_text:
            return jsonify({"error": "Projekt-ID und Anforderungstext sind erforderlich"}), 400

        #  Alle Testfälle mit der gleichen Anforderung abrufen
        test_cases = TestCase.query.filter_by(project_id=project_id, requirement_text=requirement_text).all()
        if not test_cases:
            return jsonify({"error": "Keine Testfälle für diese Anforderung gefunden"}), 404

        # KI aufrufen, um die Prioritäten für die Testfälle zu bestimmen
        raw_responses = prioritize_test_cases([tc.description for tc in test_cases])

        #  Debugging: Zeige die KI-Antwort
        print(" KI-Rohantwort:\n", raw_responses)

        #  Funktion zur Bereinigung von Testfall-Beschreibungen (nur "Voraussetzung" extrahieren)
        def extract_prerequisite(text):
            match = re.search(r"\*\*Voraussetzung:\*\*(.*?)\*\*", text)
            if match:
                return match.group(1).strip()  # Extraire le contenu après "Voraussetzung"
            return text.split(".")[0]  # Sinon, prendre la première phrase comme fallback

        #  Bereinigung der Testfallbeschreibungen in der Datenbank
        cleaned_test_cases = {extract_prerequisite(tc.description): tc for tc in test_cases}

        #  Prioritäten mit den existierenden Testfällen verknüpfen
        priority_mapping = {}

        for response in raw_responses:
            test_case_desc_ki = response["test_case"]
            priority = response["priority"].strip().lower()

            # Suche den am besten passenden Testfall aus der bereinigten DB-Liste
            closest_match = difflib.get_close_matches(test_case_desc_ki, list(cleaned_test_cases.keys()), n=1, cutoff=0.5)

            if closest_match:
                matched_test_case = cleaned_test_cases[closest_match[0]]
                priority_mapping[matched_test_case.id] = priority

        #  Prioritäten in der Datenbank aktualisieren
        updated_test_cases = []
        for test_case in test_cases:
            if test_case.id in priority_mapping:
                test_case.priority = priority_mapping[test_case.id]
                updated_test_cases.append({
                    "test_case_id": test_case.id,
                    "name": test_case.name,
                    "priority": test_case.priority
                })

        #  Änderungen in der Datenbank speichern
        db.session.commit()

        return jsonify({
            "message": "Testfälle erfolgreich priorisiert.",
            "ki_response": raw_responses,  # 🔥 KI-Volltext-Response
            "prioritized_test_cases": updated_test_cases  # ✅ Strukturierte Antwort mit DB-Werten
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Anforderungen klassifizieren (Einzeln oder Alle)
@ai_bp.route("/classify-requirements", methods=["POST"])
def classify_requirements_route():
    """
    Klassifiziert Anforderungen entweder für das gesamte Projekt oder für eine bestimmte Anforderung.
    Die Route stellt sicher, dass der Benutzer authentifiziert ist.
    """

    #  Authentifizierung prüfen
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    #  Benutzer-ID aus Token extrahieren
    created_by = decoded_token.get("uid")
    if not created_by:
        return jsonify({"error": "Benutzer-ID konnte nicht ermittelt werden"}), 403

    try:
        #  Daten aus der Anfrage abrufen
        data = request.get_json()
        project_id = data.get("project_id")
        requirement_text = data.get("requirement_text")
        classify_all = data.get("classify_all", False)  # Falls alle Anforderungen klassifiziert werden sollen

        if not project_id:
            return jsonify({"error": "Projekt-ID ist erforderlich"}), 400

        #  Projekt abrufen und Berechtigung prüfen
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404

        if project.created_by != created_by:
            return jsonify({"error": "Keine Berechtigung für dieses Projekt"}), 403

        #  Funktion zur Normalisierung der Kategorie
        def normalize_category(classification):
            category_mapping = {
                "funktional": ["funktional", "functional", "funktionelle", "funcional"],
                "nicht-funktional": ["nicht-funktional", "non-functional", "non fonctionnel", "no funcional"],
                "regression": ["regression", "regressionstest", "test der rückwärtskompatibilität"],
                "integration": ["integration", "integrationstest", "systemintegration"],
                "unit-test": ["unit test", "unit-test", "einheitentest"],
                "system-test": ["system-test", "systemtest", "gesamtsystemtest"],
                "akzeptanztest": ["akzeptanztest", "user acceptance test", "uat"],
                "lasttest": ["lasttest", "performancetest", "stresstest"],
                "sicherheitstest": ["sicherheitstest", "penetrationstest", "security test"]
            }

            classification_lower = classification.lower()
            #  Debugging: Zeige die KI-Antwort vor der Normalisierung an
            print(f" KI-Rohantwort: {classification}")

            last_word = classification_lower.split()[-1]


            for category, keywords in category_mapping.items():
                if last_word in keywords:
                    print(f" Kategorie erkannt: {category} (Schlüsselwort: {last_word})")
                    return category

            print(" Keine passende Kategorie gefunden, Rückgabe: unbekannt")
            return "unbekannt"  # Standardfall, wenn keine passende Kategorie gefunden wurde

        #  Anforderungen klassifizieren
        if classify_all:
            #  Alle Anforderungen für das Projekt abrufen
            test_cases = TestCase.query.filter_by(project_id=project_id).all()
            if not test_cases:
                return jsonify({"error": "Keine Testfälle für dieses Projekt gefunden"}), 404

            test_case_texts = [tc.requirement_text for tc in test_cases]

            #  KI zur Klassifizierung aufrufen (Streaming für Effizienz)
            classifications_raw = classify_multiple_requirements(test_case_texts)

            classifications = []
            for test_case, classification in zip(test_cases, classifications_raw):
                print(f" KI-Rohantwort für TestCase {test_case.id}: {classification}")  # Debugging

                category = normalize_category(classification)
                test_case.category = category
                classifications.append({
                    "test_case_id": test_case.id,
                    "name": test_case.name,
                    "category": test_case.category
                })

            db.session.commit()

            return jsonify({
                "message": "Alle Testfälle erfolgreich klassifiziert",
                "Ki_responses": classifications_raw,  # 🔥 KI-Volltext-Response
                "classifications": classifications
            }), 200

        else:
            if not requirement_text:
                return jsonify({"error": "Anforderungstext ist erforderlich"}), 400

            #  Nur eine spezifische Anforderung klassifizieren
            classification = classify_requirements(requirement_text)
            print(f" KI-Rohantwort vor Normalisierung: {classification}")  # Debugging

            category = normalize_category(classification)

            return jsonify({
                "message": "Anforderung erfolgreich klassifiziert",
                "Ki_response": classification,  # 🔥 KI-Volltext-Response
                "classification": category
            }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@ai_bp.route("/find-redundant-test-cases", methods=["POST"])
def find_redundant_test_cases_route():
    """
    Findet redundante Testfälle und markiert sie als redundant.
     Identifiziert redundante Testfälle mit GPT.
     Aktualisiert die Testfälle (setzt `is_redundant=True`).
    """
    #  Token-Authentifizierung prüfen
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    try:
        #  Daten abrufen
        data = request.get_json()
        project_id = data.get("project_id")
        requirement_text = data.get("requirement_text")

        if not project_id or not requirement_text:
            return jsonify({"error": "Projekt-ID und Anforderungstext sind erforderlich"}), 400

        #  Alle Testfälle mit dieser Anforderung abrufen
        test_cases = TestCase.query.filter_by(project_id=project_id, requirement_text=requirement_text).all()
        if not test_cases:
            return jsonify({"error": "Keine Testfälle für diese Anforderung gefunden"}), 404

        #  Redundante Testfälle finden
        raw_responses = find_redundant_test_cases([tc.description for tc in test_cases])

        print("KI-Rohantwort:", raw_responses)  # Debugging

        if not raw_responses or not raw_responses.get("redundant_test_cases"):
            return jsonify({
                "message": "Keine redundanten Testfälle erkannt.",
                "ki_response": raw_responses,
                "redundant_test_cases": []
            }), 200

        # dict for
        test_case_dict = {tc.description.strip(): tc for tc in test_cases}


        def normalize_text(text):
            return text.strip().lstrip("0123456789.[]").strip()

        redundant_test_case_ids = []
        for response in raw_responses["redundant_test_cases"]:
            redundant_description = normalize_text(response["redundant_test_case"])


            for existing_description, test_case in test_case_dict.items():
                if normalize_text(existing_description) == redundant_description:
                    test_case.is_redundant = True
                    redundant_test_case_ids.append(test_case.id)
                    break


        db.session.commit()

        return jsonify({
            "message": "Redundante Testfälle erfolgreich identifiziert und markiert.",
            "ki_response": raw_responses,  # 🔥 KI-Volltext-Response
            "marked_redundant_test_cases": redundant_test_case_ids  # ✅ Tests mis à jour
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Fehler beim Markieren redundanter Testfälle: {str(e)}"}), 500

