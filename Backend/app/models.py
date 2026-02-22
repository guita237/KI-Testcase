from app import db

# Benutzer-Modell
class User(db.Model):
    id = db.Column(db.String(128), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    role = db.Column(db.String(20), default="tester")  # z. B. 'admin', 'tester'
    created_at = db.Column(db.DateTime, default=db.func.now())


    # Relationen
    projects = db.relationship('Project', backref='creator', lazy=True, cascade="all, delete-orphan")
    test_cases = db.relationship('TestCase', backref='creator', lazy=True, cascade="all, delete-orphan")
    logs = db.relationship('Log', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

# Projekt-Modell
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    created_by = db.Column(db.String(128), db.ForeignKey('user.id'), nullable=False)

    # Relationen
    test_cases = db.relationship('TestCase', backref='project', lazy=True)

    def __repr__(self):
        return f"<Project {self.name}>"

# Testfall-Modell mit erweiterten Feldern
class TestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)  # Kategorie (funktional, nicht-funktional)
    priority = db.Column(db.String(20), default='medium')  # Priorität (hoch, mittel, niedrig)
    created_by = db.Column(db.String(128), db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    is_redundant = db.Column(db.Boolean, default=False)  # Redundanzstatus
    test_script = db.Column(db.Text, nullable=True)  # Automatisierter Testcode
    requirement_text = db.Column(db.Text, nullable=True)  #  NEU: Speichert die Anforderung für den Testfall

    # Relationen
    ki_suggestions = db.relationship('KISuggestion', backref='test_case', lazy=True)

    def __repr__(self):
        return f"<TestCase {self.name}>"

# Codeänderungen-Modell
class CodeChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(200), nullable=False)
    lines_changed = db.Column(db.Integer, nullable=False)
    commit_id = db.Column(db.String(50), nullable=False)  # Verknüpft mit einem Repository-Commit
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<CodeChange {self.file_name}>"

# KI-Vorschläge-Modell
class KISuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    suggestion_type = db.Column(db.String(50), nullable=False)  # z. B. 'prioritization', 'generation'
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<KISuggestion {self.suggestion_type}>"

# Log-Modell
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<Log {self.action}>"


class RAGReference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requirement_text = db.Column(db.Text, nullable=False)
    test_case_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=True)  # Ex: Sicherheit, UI, etc.
    created_at = db.Column(db.DateTime, default=db.func.now())
    embedding = db.Column(db.PickleType, nullable=True)

    def __repr__(self):
        return f"<RAGReference id={self.id}>"
