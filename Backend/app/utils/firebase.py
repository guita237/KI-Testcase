import firebase_admin
from firebase_admin import credentials, auth
import os

# Firebase initialisieren
def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")  # Verwendet die Umgebungsvariable
        if not cred_path:
            raise EnvironmentError("FIREBASE_CREDENTIALS_PATH ist nicht gesetzt.")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

# Token verifizieren
def verify_token(token):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Fehler beim Verifizieren des Tokens: {e}")
        return None
