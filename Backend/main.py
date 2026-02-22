from app import create_app, db
import sys
import logging
from  flask_cors import CORS

#  Logging für Docker sofort aktivieren
sys.stdout = sys.stderr
sys.stdout.reconfigure(line_buffering=True)
logging.basicConfig(level=logging.DEBUG)

print(" Logging aktiviert! Docker zeigt nun alle `print()`-Befehle sofort an.")

app = create_app()

# aktiviere CORS
CORS(app, resources={r"/*": {"origins": "*"}})  # Erlaube alle Ursprünge

#  Überprüfung der Datenbank-Tabellen
with app.app_context():
    tables = db.inspect(db.engine).get_table_names()
    print(" Tabellen in der Datenbank:", tables)

if __name__ == "__main__":
    print("⚡ Flask-Backend läuft jetzt mit Gunicorn!")  #  Kein `app.run()` nötig!
