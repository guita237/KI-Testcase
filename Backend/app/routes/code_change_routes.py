from flask import Blueprint, request, jsonify
from app.models import db, CodeChange
from app.utils import verify_token


code_bp = Blueprint("code_change_routes", __name__)


### GET: Alle Code-Änderungen abrufen ###
@code_bp.route("/code-changes", methods=["GET"])
def get_code_changes():
    """
    Gibt alle Code-Änderungen zurück. Nur der Eigentümer kann seine Code-Änderungen sehen.
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

    # Code-Änderungen abrufen, die von diesem Nutzer erstellt wurden
    code_changes = CodeChange.query.filter_by(commit_id=user_id).all()

    if not code_changes:
        return jsonify({"message": "Keine Code-Änderungen gefunden"}), 200

    return jsonify([{
        "id": cc.id,
        "file_name": cc.file_name,
        "lines_changed": cc.lines_changed,
        "commit_id": cc.commit_id,
        "description": cc.description,
        "created_at": cc.created_at
    } for cc in code_changes]), 200


###  DELETE: Eine Code-Änderung löschen ###
@code_bp.route("/code-changes/<int:change_id>", methods=["DELETE"])
def delete_code_change(change_id):
    """
    Löscht eine Code-Änderung, falls der Nutzer der Eigentümer ist.
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

    # Code-Änderung abrufen
    code_change = CodeChange.query.get(change_id)
    if not code_change:
        return jsonify({"error": "Code-Änderung nicht gefunden"}), 404

    if code_change.commit_id != user_id:
        return jsonify({"error": "Keine Berechtigung zum Löschen dieser Code-Änderung"}), 403

    db.session.delete(code_change)
    db.session.commit()

    return jsonify({"message": "Code-Änderung erfolgreich gelöscht"}), 200