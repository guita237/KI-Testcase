from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os

# Blurprint für Datei-Routen

datei_bp = Blueprint("datei_routes", __name__)

UPLOAD_FOLDER = "uploads/"
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Hilfsfunktion: Datei-Validierung
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Route: Datei hochladen
@datei_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Dateiname fehlt"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        return jsonify({"message": "Datei erfolgreich hochgeladen", "filepath": filepath}), 200
    return jsonify({"error": "Ungültiger Dateityp"}), 400

# Route: Datei herunterladen
@datei_bp.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({"error": "Datei nicht gefunden"}), 404