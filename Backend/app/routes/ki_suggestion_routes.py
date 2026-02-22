from flask import Blueprint, request, jsonify
from app.models import db, KISuggestion, TestCase
from app.utils import verify_token


ki_suggestion_bp = Blueprint("ki_suggestion_routes", __name__)

###  GET: Alle KI-Vorschläge abrufen ###
@ki_suggestion_bp.route("/ki-suggestions", methods=["GET"])
def get_ki_suggestions():
    """
    Gibt alle KI-Vorschläge zurück. Nur der Nutzer kann die Vorschläge zu seinen Testfällen sehen.
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

    # KI-Vorschläge abrufen, die zu den Testfällen des Nutzers gehören
    ki_suggestions = KISuggestion.query.join(TestCase).filter(TestCase.created_by == user_id).all()

    if not ki_suggestions:
        return jsonify({"message": "Keine KI-Vorschläge gefunden"}), 200

    return jsonify([{
        "id": ki.id,
        "test_case_id": ki.test_case_id,
        "suggestion_type": ki.suggestion_type,
        "description": ki.description,
        "created_at": ki.created_at
    } for ki in ki_suggestions]), 200


###  DELETE: Einen KI-Vorschlag löschen ###
@ki_suggestion_bp.route("/ki-suggestions/<int:suggestion_id>", methods=["DELETE"])
def delete_ki_suggestion(suggestion_id):
    """
    Löscht einen KI-Vorschlag, falls der Nutzer der Eigentümer des Testfalls ist.
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

    # KI-Vorschlag abrufen
    ki_suggestion = KISuggestion.query.get(suggestion_id)
    if not ki_suggestion:
        return jsonify({"error": "KI-Vorschlag nicht gefunden"}), 404

    # Prüfen, ob der Nutzer berechtigt ist, den Vorschlag zu löschen
    test_case = TestCase.query.get(ki_suggestion.test_case_id)
    if not test_case or test_case.created_by != user_id:
        return jsonify({"error": "Keine Berechtigung zum Löschen dieses KI-Vorschlags"}), 403

    db.session.delete(ki_suggestion)
    db.session.commit()

    return jsonify({"message": "KI-Vorschlag erfolgreich gelöscht"}), 200