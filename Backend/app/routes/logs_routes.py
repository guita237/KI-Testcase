from flask import Blueprint, request, jsonify
from app import db
from app.models import Log, User
from app.utils.firebase import verify_token

# Blueprint für Log-Routen
log_bp = Blueprint("log_routes", __name__)


# Hilfsfunktion : Authentifizierung prüefen
def get_authenticated_user():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer"):
        return None, jsonify({"error": "Fehlendes oder ungültiges Token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_token(id_token)

    if not decoded_token:
        return None, jsonify({"error": "Token konnte nicht verifiziert werden"}), 403

    user_id = decoded_token.get("uid")
    if not user_id:
        return None, jsonify({"error": "Benutzer-ID konnte nicht ermittelt werden"}), 403

    return user_id, None

# Route: Alle Logs eines Benutzers abrufen
@log_bp.route("/logs/user", methods=["GET"])
def get_user_logs():
    """
    Gibt alle Logs eines bestimmten Benutzers zurück.
    """
    user_id, auth_error = get_authenticated_user()
    if auth_error:
        return auth_error

    try:
        # Überprüfen, ob der Benutzer existiert
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Benutzer nicht gefunden"}), 404

        # Logs des Benutzers abrufen
        logs = Log.query.filter_by(user_id=user_id).order_by(Log.created_at.desc()).all()
        log_list = [{"id": log.id, "action": log.action, "description": log.description, "created_at": log.created_at} for log in logs]

        return jsonify({"logs": log_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Alle Logs abrufen (optional: nach Aktion filtern)
@log_bp.route("/logs", methods=["GET"])
def get_all_logs():
    """
    Gibt alle Logs zurück (optional gefiltert nach Aktion).
    """
    action_filter = request.args.get("action")  # Optionaler Filter nach Aktion

    try:
        if action_filter:
            logs = Log.query.filter_by(action=action_filter).order_by(Log.created_at.desc()).all()
        else:
            logs = Log.query.order_by(Log.created_at.desc()).all()

        log_list = [{"id": log.id, "user_id": log.user_id, "action": log.action, "description": log.description, "created_at": log.created_at} for log in logs]

        return jsonify({"logs": log_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Logdetails abrufen
@log_bp.route("/log/<int:log_id>", methods=["GET"])
def get_log_details(log_id):
    """
    Gibt die Details eines spezifischen Logs zurück.
    """
    try:
        log = Log.query.get(log_id)
        if not log:
            return jsonify({"error": "Log nicht gefunden"}), 404

        log_details = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "description": log.description,
            "created_at": log.created_at
        }
        return jsonify({"log": log_details}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Logeinträge löschen (nach ID oder Benutzer)
@log_bp.route("/delete-logs", methods=["DELETE"])
def delete_logs():
    """
    Löscht Logs basierend auf einer Log-ID oder Benutzer-ID.
    """
    data = request.get_json()
    log_id = data.get("log_id")
    user_id = data.get("user_id")

    try:
        if log_id:
            # Einzelnen Logeintrag löschen
            log = Log.query.get(log_id)
            if not log:
                return jsonify({"error": "Log nicht gefunden"}), 404

            db.session.delete(log)

        elif user_id:
            # Alle Logs eines Benutzers löschen
            logs = Log.query.filter_by(user_id=user_id).all()
            if not logs:
                return jsonify({"error": "Keine Logs für diesen Benutzer gefunden"}), 404

            for log in logs:
                db.session.delete(log)

        else:
            return jsonify({"error": "Log-ID oder Benutzer-ID erforderlich"}), 400

        db.session.commit()
        return jsonify({"message": "Logs erfolgreich gelöscht"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
