from flask import Blueprint, request, jsonify, render_template
from firebase_admin import auth
from app import db
from app.models import User, Log
from app.utils.firebase import verify_token
from app.utils import send_verification_email, send_reset_password, send_modification_email
from dotenv import load_dotenv
import os
import requests


auth_bp = Blueprint('auth', __name__)

# .env-Datei laden
load_dotenv()

# Firebase API Key abrufen
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL")


###  Geschützte API mit Token-Prüfung
@auth_bp.route("/secure-endpoint", methods=["GET"])
def secure_endpoint():
    user_id = verify_token(request)
    if not user_id:
        return jsonify({"message": "Ungültiges oder fehlendes Token"}), 401

    return jsonify({"message": "Erfolgreich authentifiziert", "user_id": user_id}), 200


###  Benutzerregistrierung mit Firebase
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    try:
        # Benutzer in Firebase erstellen
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        # Einstellungen für den Aktionscode
        action_code_settings = auth.ActionCodeSettings(
            url=f'{FRONTEND_URL}/api/auth/confirm-email?email={email}',
            handle_code_in_app=True
        )

        # E-Mail-Verifizierungslink generieren & senden
        verification_link = auth.generate_email_verification_link(email,action_code_settings)
        send_verification_email(name, email, verification_link)

        return jsonify({
            'message': 'Ein Verifizierungslink wurde an Ihre E-Mail-Adresse gesendet.',
            'firebase_uid': user_record.uid,
            'email': email
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

###  E-Mail-Bestätigung
@auth_bp.route('/confirm-email', methods=['GET'])
def confirm_email():
    email = request.args.get('email')
    if not email:
        return render_template('message.html', message=" Ungültige E-Mail-Adresse!"), 400

    try:
        # Überprüfen, ob die E-Mail in Firebase existiert
        user_record = auth.get_user_by_email(email)

        # Prüfen ob Email in Firebase verifiziert ist
        if not user_record.email_verified:
            return render_template('message.html', message=" E-Mail wurde noch nicht verifiziert. Bitte überprüfen Sie Ihr Postfach."), 400

        # Benutzer in lokaler Datenbank speichern (falls nicht vorhanden)
        user = User.query.get(user_record.uid)
        if not user:
            new_user = User(
                id=user_record.uid,
                email=email,
                name=user_record.display_name or "User",
                role='tester'
            )
            db.session.add(new_user)
            db.session.commit()

            # Log für neuen Benutzer
            log = Log(user_id=new_user.id, action="USER_CREATED", description="User created via email verification")
            db.session.add(log)
            db.session.commit()

            return render_template('message.html', message=" E-Mail erfolgreich bestätigt! Ihr Konto wurde erstellt. Sie können sich jetzt einloggen."), 200
        else:
            # Log für bestehenden Benutzer
            log = Log(user_id=user.id, action="EMAIL_VERIFIED", description="Email verified")
            db.session.add(log)
            db.session.commit()

            return render_template('message.html', message=" E-Mail bereits bestätigt! Sie können sich jetzt einloggen."), 200

    except auth.UserNotFoundError:
        return render_template('message.html', message=" Benutzer mit dieser E-Mail existiert nicht in Firebase."), 404
    except Exception as e:
        print(f" Fehler bei E-Mail-Bestätigung: {str(e)}")
        return render_template('message.html', message=f" Ein Fehler ist aufgetreten: {str(e)}"), 400

###  Benutzer-Login
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authentifiziert einen Benutzer mit Firebase-Login.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'E-Mail und Passwort sind erforderlich'}), 400

    try:
        # Firebase-Login
        firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
        response = requests.post(firebase_url, json={"email": email, "password": password, "returnSecureToken": True})

        if response.status_code != 200:
            return jsonify({'error': 'Ungültige Anmeldedaten'}), 401

        response_data = response.json()
        user_id = response_data.get('localId')

        # Prüfen, ob Benutzer in lokaler Datenbank existiert
        if not User.query.get(user_id):
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404

        return jsonify({
            'message': 'Login erfolgreich',
            'user_id': user_id,
            'token': response_data.get('idToken')  # ID-Token zurückgeben
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


###  Google-Login / Registrierung
@auth_bp.route('/google-register', methods=['POST'])
def google_register():
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        if not id_token:
            return jsonify({'error': 'ID token fehlt'}), 400

        # Token verifizieren
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name')

        # Benutzer in lokaler Datenbank speichern, falls nicht vorhanden
        if not User.query.get(user_id):
            new_user = User(id=user_id, email=email, name=name)
            db.session.add(new_user)
            db.session.commit()
            message = 'Benutzer erfolgreich registriert'
        else:
            message = 'Benutzer erfolgreich angemeldet'

        return jsonify({'message': message, 'user_id': user_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


###  Benutzer löschen (mit CASCADE)
@auth_bp.route('/delete-user', methods=['DELETE'])
def delete_user():
    # Extraire le token du header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token fehlt oder ist ungültig"}), 401

    token = auth_header.split(' ')[1]  # Récupère "Bearer TOKEN" -> "TOKEN"

    #  Passer le token string directement
    decoded_token = verify_token(token)
    if not decoded_token:
        return jsonify({"error": "Ungültiges Token"}), 401

    user_id = decoded_token['uid']  # Extraire l'UID du token décodé

    try:
        # Firebase löschen
        auth.delete_user(user_id)

        # DB löschen
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()

        return jsonify({'message': 'Benutzer erfolgreich gelöscht'}), 200

    except Exception as e:
        print(f" Fehler beim Löschen: {e}")
        return jsonify({'error': str(e)}), 500

###  E-Mail-Adresse aktualisieren
@auth_bp.route('/update-email', methods=['POST'])
def update_email():
    """
    Aktualisiert die E-Mail-Adresse eines Benutzers in Firebase.
    """
    user_id = verify_token(request)
    if not user_id:
        return jsonify({"error": "Ungültiges oder fehlendes Token"}), 401

    data = request.get_json()
    new_email = data.get('new_email')

    if not new_email:
        return jsonify({"error": "Neue E-Mail-Adresse ist erforderlich"}), 400

    try:
        auth.update_user(user_id, email=new_email)
        verification_link = auth.generate_email_verification_link(new_email)
        send_modification_email(new_email, new_email, verification_link)

        return jsonify({"message": "E-Mail-Adresse aktualisiert und Bestätigungslink gesendet"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


###  Passwort zurücksetzen
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Sendet einen Passwort-Zurücksetzungslink an die E-Mail-Adresse des Benutzers.
    """
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "E-Mail-Adresse ist erforderlich"}), 400

    try:
        reset_link = auth.generate_password_reset_link(email)
        send_reset_password(email, email, reset_link)

        return jsonify({"message": "Passwort-Zurücksetzungslink gesendet"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
