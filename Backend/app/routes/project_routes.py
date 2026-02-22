from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Project, Log
from app.utils import verify_token

# Blueprint für Projekt-Routen
project_bp = Blueprint("project_routes", __name__)

#  Hilfsfunktion: Authentifizierung prüfen
def get_authenticated_user():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)

    if not decoded_token:
        return None, jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")
    if not user_id:
        return None, jsonify({"error": "Benutzer-ID konnte nicht ermittelt werden"}), 403

    return user_id, None

#  Route: Neues Projekt erstellen
@project_bp.route("/create-project", methods=["POST"])
def create_project():
    """
    Erstellt ein neues Projekt für den angemeldeten Benutzer.
    Die Benutzer-ID wird aus dem Firebase-Token extrahiert.
    """
    user_id, auth_error = get_authenticated_user()
    if auth_error:
        return auth_error

    data = request.get_json()
    project_name = data.get("name")
    project_description = data.get("description", "")

    if not project_name:
        return jsonify({"error": "Projektname ist erforderlich"}), 400

    try:
        # Neues Projekt erstellen
        new_project = Project(
            name=project_name,
            description=project_description,
            created_by=user_id  #  Benutzer-ID aus Token
        )
        db.session.add(new_project)

        # Log-Eintrag
        log_entry = Log(
            user_id=user_id,
            action="Projekt erstellt",
            description=f"Projekt '{project_name}' wurde erstellt."
        )
        db.session.add(log_entry)
        db.session.commit()

        return jsonify({"message": "Projekt erfolgreich erstellt", "project_id": new_project.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#  Route: Alle Projekte des authentifizierten Benutzers abrufen
@project_bp.route("/user-projects", methods=["GET"])
def get_user_projects():
    """
    Gibt alle Projekte des angemeldeten Benutzers zurück.
    """
    user_id, auth_error = get_authenticated_user()
    if auth_error:
        return auth_error

    try:
        # Projekte des Benutzers abrufen
        projects = Project.query.filter_by(created_by=user_id).all()
        project_list = [
            {"id": p.id, "name": p.name, "description": p.description, "created_at": p.created_at}
            for p in projects
        ]
        return jsonify({"projects": project_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Projektinformationen abrufen
@project_bp.route("/project/<int:project_id>", methods=["GET"])
def get_project(project_id):
    """
    Gibt die Details eines bestimmten Projekts zurück.
    """
    user_id, auth_error = get_authenticated_user()
    if auth_error:
        return auth_error

    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404

        #  Zugriff prüfen
        if project.created_by != user_id:
            return jsonify({"error": "Keine Berechtigung für dieses Projekt"}), 403

        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_by": project.created_by,
            "created_at": project.created_at
        }
        return jsonify({"project": project_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#  Route: Projekt aktualisieren
@project_bp.route("/update-project/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    """
    Aktualisiert ein Projekt.
    """
    user_id, auth_error = get_authenticated_user()
    if auth_error:
        return auth_error

    data = request.get_json()
    project_name = data.get("name")
    project_description = data.get("description")

    if not project_name:
        return jsonify({"error": "Projektname ist erforderlich"}), 400

    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404

        # Zugriff prüfen
        if project.created_by != user_id:
            return jsonify({"error": "Keine Berechtigung zur Bearbeitung dieses Projekts"}), 403

        project.name = project_name
        project.description = project_description
        db.session.commit()

        return jsonify({"message": "Projekt erfolgreich aktualisiert"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Projekt löschen
@project_bp.route("/delete-project/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    """
    Löscht ein Projekt.
    """
    user_id, auth_error = get_authenticated_user()
    if auth_error:
        return auth_error

    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404

        # Zugriff prüfen
        if project.created_by != user_id:
            return jsonify({"error": "Keine Berechtigung zum Löschen dieses Projekts"}), 403

        db.session.delete(project)

        # Log-Eintrag
        log_entry = Log(
            user_id=user_id,
            action="Projekt gelöscht",
            description=f"Projekt '{project.name}' wurde gelöscht."
        )
        db.session.add(log_entry)
        db.session.commit()

        return jsonify({"message": "Projekt erfolgreich gelöscht"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
