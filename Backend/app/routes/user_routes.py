from flask import Blueprint, request, jsonify
from firebase_admin import auth
from app import db
from app.models import User
from app.utils.firebase import verify_token  # Importiere die Token-Verifizierung

user_bp = Blueprint('user', __name__)

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



# Route: Benutzerdaten aktualisieren
@user_bp.route('/update-user', methods=['PUT'])
def update_user():
    """
    Aktualisiert die Informationen eines Benutzers (Name, Telefonnummer, Rolle).

    """
    user_id, auth_error = get_authenticated_user()
    if auth_error:
        return auth_error


    data = request.get_json()
    name = data.get('name')
    phone_number = data.get('phone_number')
    role = data.get('role')

    try:
        # Benutzer in der Datenbank suchen
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Benutzer nicht gefunden"}), 404

        # Benutzerdaten aktualisieren
        if name:
            user.name = name
        if phone_number:
            user.phone_number = phone_number
        if role:
            user.role = role

        db.session.commit()

        return jsonify({
            "message": "Benutzerdaten erfolgreich aktualisiert",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone_number": user.phone_number,
                "role": user.role
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Fehler beim Aktualisieren der Benutzerdaten: {str(e)}"}), 500



# Route: Benutzerdetails abrufen
@user_bp.route('/get-user', methods=['GET'])
def get_user():
    """
    Ruft die Details eines Benutzers anhand des Firebase-ID-Tokens ab.
    """
    user_id, auth_error = get_authenticated_user()
    if auth_error:
        return auth_error

    try:
        # Benutzer in der Datenbank suchen
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Benutzer nicht gefunden"}), 404

        return jsonify({
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone_number": user.phone_number,
                "role": user.role,
                "created_at": user.created_at
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Fehler beim Abrufen der Benutzerdetails: {str(e)}"}), 500



# Route: Benutzerrolle aktualisieren
@user_bp.route('/update-role', methods=['PUT'])
def update_role():
    """
    Aktualisiert die Rolle eines Benutzers.
    Authentifizierung erfolgt über Firebase-ID-Token.
    """
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Authentifizierung erforderlich"}), 401

    user_data = verify_token(token)  # Token verifizieren
    if not user_data:
        return jsonify({"error": "Ungültiges Token"}), 401

    firebase_uid = user_data.get("uid")

    data = request.get_json()
    new_role = data.get('role')

    if not new_role:
        return jsonify({"error": "Neue Rolle ist erforderlich"}), 400

    try:
        # Benutzer in der Datenbank suchen
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if not user:
            return jsonify({"error": "Benutzer nicht gefunden"}), 404

        # Benutzerrolle aktualisieren
        user.role = new_role
        db.session.commit()

        return jsonify({"message": "Benutzerrolle erfolgreich aktualisiert", "new_role": new_role}), 200

    except Exception as e:
        return jsonify({"error": f"Fehler beim Aktualisieren der Benutzerrolle: {str(e)}"}), 500
