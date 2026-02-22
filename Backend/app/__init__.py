from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config  # Import aus app/config.py
from dotenv import load_dotenv  # <--- Import für dotenv
import os

# Lade Umgebungsvariablen aus .env
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Überprüfe, ob DATABASE_URL korrekt geladen wurde
    print("Geladene Datenbank-URL:", app.config["SQLALCHEMY_DATABASE_URI"])

    # Importiere Modelle
    with app.app_context():
        from app import models

    # Routen am Ende registrieren
    from app.routes import routes_bp
    app.register_blueprint(routes_bp)

    @app.route("/health")
    def health_check():
      return jsonify(status="healthy"), 200

    return app
