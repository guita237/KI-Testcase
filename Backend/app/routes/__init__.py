from flask import Blueprint

# Erstellen Sie ein Blueprint für Routen
routes_bp = Blueprint("routes", __name__)

# Importieren Sie spezifische Routen
from .auth_routes import auth_bp
from .test_case_routes import test_case_bp
from .ai_routes import ai_bp
from  .logs_routes import log_bp
from .project_routes import project_bp
from .user_routes import user_bp
from .code_change_routes import code_bp
from .ki_suggestion_routes import ki_suggestion_bp


# Registrieren Sie die einzelnen Blueprints in der Haupt-Blueprint
routes_bp.register_blueprint(auth_bp, url_prefix="/auth")
routes_bp.register_blueprint(test_case_bp, url_prefix="/test")
routes_bp.register_blueprint(ai_bp, url_prefix="/ai")
routes_bp.register_blueprint(log_bp, url_prefix="/logs")
routes_bp.register_blueprint(project_bp, url_prefix="/projects")
routes_bp.register_blueprint(user_bp, url_prefix="/users")
routes_bp.register_blueprint(code_bp, url_prefix="/code")
routes_bp.register_blueprint(ki_suggestion_bp, url_prefix="/ki-suggestions")