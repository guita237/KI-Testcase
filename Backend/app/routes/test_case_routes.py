from flask import Blueprint, request, jsonify
from app.models import db, TestCase, Project, User
from app.utils import verify_token

test_case_bp = Blueprint("test_routes", __name__)

###  GET-ROUTEN (Abrufen von Testfällen) ###

#  1. Alle Testfälle abrufen (nur für eigene Projekte)
@test_case_bp.route("/test-cases", methods=["GET"])
def get_all_test_cases():
    """
    Gibt eine Liste aller Testfälle zurück, die zu den Projekten des Nutzers gehören.
    Erfordert Authentifizierung.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")

    # Nur Testfälle aus Projekten des Nutzers abrufen
    test_cases = TestCase.query.join(Project).filter(Project.created_by == user_id).all()

    return jsonify([{
        "id": tc.id,
        "name": tc.name,
        "description": tc.description,
        "category": tc.category,
        "priority": tc.priority,
        "project_id": tc.project_id,
        "is_redundant": tc.is_redundant,
        "requirement_text": tc.requirement_text
    } for tc in test_cases]), 200


#  2. Einzelnen Testfall nach ID abrufen (nur wenn der Nutzer berechtigt ist)
@test_case_bp.route("/test-cases/<int:test_case_id>", methods=["GET"])
def get_test_case_by_id(test_case_id):
    """
    Gibt die Details eines Testfalls zurück, wenn der Nutzer berechtigt ist.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")
    test_case = TestCase.query.get(test_case_id)

    if not test_case:
        return jsonify({"error": "Testfall nicht gefunden"}), 404

    # Prüfen, ob der Nutzer Zugriff hat
    project = Project.query.get(test_case.project_id)
    if project.created_by != user_id:
        return jsonify({"error": "Zugriff verweigert"}), 403

    return jsonify({
        "id": test_case.id,
        "name": test_case.name,
        "description": test_case.description,
        "category": test_case.category,
        "priority": test_case.priority,
        "project_id": test_case.project_id,
        "is_redundant": test_case.is_redundant,
        "requirement_text": test_case.requirement_text
    }), 200


#  3. Alle Testfälle eines Projekts abrufen (nur wenn der Nutzer berechtigt ist)
@test_case_bp.route("/test-cases/project/<int:project_id>", methods=["GET"])
def get_test_cases_by_project(project_id):
    """
    Gibt alle Testfälle eines Projekts zurück, falls der Nutzer berechtigt ist.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")
    project = Project.query.get(project_id)

    if not project or project.created_by != user_id:
        return jsonify({"error": "Projekt nicht gefunden oder Zugriff verweigert"}), 403

    test_cases = TestCase.query.filter_by(project_id=project_id).all()

    return jsonify([{
        "id": tc.id,
        "name": tc.name,
        "description": tc.description,
        "category": tc.category,
        "priority": tc.priority,
        "is_redundant": tc.is_redundant,
        "requirement_text": tc.requirement_text
    } for tc in test_cases]), 200

###  GET: Redundante Testfälle abrufen ###
@test_case_bp.route("/test-cases/redundant", methods=["GET"])
def get_redundant_test_cases():
    """
    Gibt alle als redundant markierten Testfälle zurück, die zu den Projekten des Nutzers gehören.
    Erfordert Authentifizierung.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")

    # Nur Testfälle aus Projekten des Nutzers abrufen
    test_cases = TestCase.query.join(Project).filter(Project.created_by == user_id, TestCase.is_redundant == True).all()

    if not test_cases:
        return jsonify({"message": "Keine redundanten Testfälle gefunden"}), 200

    return jsonify([{
        "id": tc.id,
        "name": tc.name,
        "description": tc.description,
        "category": tc.category,
        "priority": tc.priority,
        "project_id": tc.project_id,
    } for tc in test_cases]), 200


###  GET: Testfälle nach Priorität abrufen ###
@test_case_bp.route("/test-cases/priority/<string:priority>", methods=["GET"])
def get_test_cases_by_priority(priority):
    """
    Gibt alle Testfälle einer bestimmten Priorität zurück, falls der Nutzer berechtigt ist.
    Erfordert Authentifizierung.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")

    # Prüfen, ob die Priorität gültig ist
    valid_priorities = ["hoch", "mittel", "niedrig"]
    if priority.lower() not in valid_priorities:
        return jsonify({"error": "Ungültige Priorität. Erlaubte Werte: hoch, mittel, niedrig"}), 400

    # Testfälle mit der angegebenen Priorität abrufen
    test_cases = TestCase.query.join(Project).filter(Project.created_by == user_id, TestCase.priority == priority).all()

    if not test_cases:
        return jsonify({"message": "Keine Testfälle mit dieser Priorität gefunden"}), 200

    return jsonify([{
        "id": tc.id,
        "name": tc.name,
        "description": tc.description,
        "category": tc.category,
        "priority": tc.priority,
        "project_id": tc.project_id,
    } for tc in test_cases]), 200


### GET: Testfälle nach requirement_text abrufen ###
@test_case_bp.route("/test-cases/requirement", methods=["GET"])
def get_test_cases_by_requirement_text():
    """
    Gibt alle Testfälle zurück, die mit einem bestimmten `requirement_text` verknüpft sind.
    Erfordert Authentifizierung.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")
    requirement_text = request.args.get("requirement_text", "").strip()

    if not requirement_text:
        return jsonify({"error": "Ein `requirement_text` ist erforderlich"}), 400

    # Testfälle mit dem angegebenen `requirement_text` abrufen
    test_cases = TestCase.query.join(Project).filter(
        Project.created_by == user_id, TestCase.requirement_text == requirement_text
    ).all()

    if not test_cases:
        return jsonify({"message": "Keine Testfälle mit diesem requirement_text gefunden"}), 200

    return jsonify([{
        "id": tc.id,
        "name": tc.name,
        "description": tc.description,
        "category": tc.category,
        "priority": tc.priority,
        "is_redundant": tc.is_redundant,
        "requirement_text": tc.requirement_text
    } for tc in test_cases]), 200


###  DELETE-ROUTEN (Löschen von Testfällen) ###

#  4. Einzelnen Testfall nach ID löschen (nur wenn der Nutzer berechtigt ist)
@test_case_bp.route("/test-cases/<int:test_case_id>", methods=["DELETE"])
def delete_test_case(test_case_id):
    """
    Löscht einen einzelnen Testfall, falls der Nutzer berechtigt ist.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")
    test_case = TestCase.query.get(test_case_id)

    if not test_case:
        return jsonify({"error": "Testfall nicht gefunden"}), 404

    project = Project.query.get(test_case.project_id)
    if project.created_by != user_id:
        return jsonify({"error": "Zugriff verweigert"}), 403

    db.session.delete(test_case)
    db.session.commit()

    return jsonify({"message": f"Testfall {test_case_id} erfolgreich gelöscht"}), 200


#  5. Alle Testfälle eines Projekts löschen (nur wenn der Nutzer berechtigt ist)
@test_case_bp.route("/test-cases/project/<int:project_id>", methods=["DELETE"])
def delete_test_cases_by_project(project_id):
    """
    Löscht alle Testfälle eines Projekts, falls der Nutzer berechtigt ist.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")
    project = Project.query.get(project_id)

    if not project or project.created_by != user_id:
        return jsonify({"error": "Projekt nicht gefunden oder Zugriff verweigert"}), 403

    test_cases = TestCase.query.filter_by(project_id=project_id).all()

    if not test_cases:
        return jsonify({"error": "Keine Testfälle für dieses Projekt gefunden"}), 404

    for test_case in test_cases:
        db.session.delete(test_case)

    db.session.commit()

    return jsonify({"message": f"Alle Testfälle für Projekt {project_id} wurden gelöscht"}), 200

@test_case_bp.route("/delete-redundant-test-cases", methods=["DELETE"])
def delete_redundant_test_cases():
    """
    Löscht alle Testfälle, die als redundant markiert sind (`is_redundant=True`).
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
        #  Alle redundanten Testfälle abrufen
        redundant_test_cases = TestCase.query.filter_by(is_redundant=True).all()

        if not redundant_test_cases:
            return jsonify({"message": "Keine redundanten Testfälle gefunden."}), 200

        #  Löschen der redundanten Testfälle
        deleted_test_case_ids = [tc.id for tc in redundant_test_cases]
        for test_case in redundant_test_cases:
            db.session.delete(test_case)

        db.session.commit()  # 🔥 Änderungen in der Datenbank speichern

        return jsonify({
            "message": "Redundante Testfälle erfolgreich gelöscht.",
            "deleted_test_cases": deleted_test_case_ids
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Fehler beim Löschen redundanter Testfälle: {str(e)}"}), 500

#  6. Alle Requirement-Text-Einträge eines Projekts abrufen
@test_case_bp.route("/requirements/project/<int:project_id>", methods=["GET"])
def get_requirements_by_project(project_id):
    """
    Gibt eine Liste aller requirement_text-Werte eines Projekts zurück (ohne Duplikate),
    falls der Nutzer berechtigt ist.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")
    project = Project.query.get(project_id)

    if not project or project.created_by != user_id:
        return jsonify({"error": "Projekt nicht gefunden oder Zugriff verweigert"}), 403

    # Alle requirement_text-Werte abrufen, wobei None ausgeschlossen und Duplikate entfernt werden
    requirements = (
        db.session.query(TestCase.requirement_text)
        .filter(TestCase.project_id == project_id, TestCase.requirement_text.isnot(None))
        .distinct()
        .all()
    )

    requirement_list = [r[0] for r in requirements]

    return jsonify({"requirements": requirement_list}), 200
