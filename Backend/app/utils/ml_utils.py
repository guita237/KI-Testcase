import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

# 📂 Verzeichnis für ML-Modelle
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "random_forest_model.pkl")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")

#  Erstelle das Modellverzeichnis, falls nicht vorhanden
os.makedirs(MODEL_DIR, exist_ok=True)


# ** Funktion: Trainiere und speichere das Modell**
def train_and_save_model(test_cases, labels):
    """
    Trainiert ein Random-Forest-Modell zur Testfall-Priorisierung und speichert es.

    :param test_cases: Liste von Testfallbeschreibungen.
    :param labels: Labels für die Testfälle (0 = niedrig, 1 = mittel, 2 = hoch).
    """
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(test_cases)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, labels)

    # Speichere Modell & Vektorisierer
    with open(MODEL_PATH, "wb") as model_file:
        pickle.dump(model, model_file)
    with open(VECTORIZER_PATH, "wb") as vec_file:
        pickle.dump(vectorizer, vec_file)

    print(" Modell und Vektorisierer erfolgreich gespeichert!")


# ** Funktion: Lade das Modell**
def load_model():
    """
    Lädt das trainierte Modell und den Vektorisierer aus der Festplatte.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        print(" Kein trainiertes Modell gefunden. Trainiere es zuerst!")
        return None, None

    with open(MODEL_PATH, "rb") as model_file:
        model = pickle.load(model_file)
    with open(VECTORIZER_PATH, "rb") as vec_file:
        vectorizer = pickle.load(vec_file)

    return model, vectorizer


# ** Funktion: Redundanzanalyse mit ML**
def find_redundant_tests_ml(test_cases):
    """
    Verwendet ein trainiertes Modell zur Erkennung redundanter Testfälle.

    :param test_cases: Liste von Testfallbeschreibungen.
    :return: Liste redundanter Testfälle.
    """
    model, vectorizer = load_model()
    if model is None or vectorizer is None:
        return " Kein trainiertes Modell gefunden. Trainiere es zuerst!"

    X = vectorizer.transform(test_cases)
    predictions = model.predict(X)

    redundant_cases = [test_cases[i] for i in range(len(predictions)) if predictions[i] == 1]
    return redundant_cases


# ** Funktion: Testfall-Kategorisierung mit ML**
def predict_category(text):
    """
    Klassifiziert einen Testfall als funktional oder nicht-funktional.

    :param text: Testfallbeschreibung.
    :return: Kategorie des Testfalls ('funktional' oder 'nicht-funktional').
    """
    model, vectorizer = load_model()
    if model is None or vectorizer is None:
        return " Kein trainiertes Modell gefunden."

    X = vectorizer.transform([text])
    prediction = model.predict(X)
    category_mapping = {0: "funktional", 1: "nicht-funktional"}
    return category_mapping.get(prediction[0], "unbekannt")


# ** Funktion: Priorisierung von Testfällen mit ML**
def prioritize_test_cases_with_ml(test_cases):
    """
    Priorisiert Testfälle basierend auf ML-Analyse.

    :param test_cases: Liste von Testfällen.
    :return: Liste priorisierter Testfälle mit Prioritätsstufen.
    """
    model, vectorizer = load_model()
    if model is None or vectorizer is None:
        return [{"test_case": tc, "priority": "Modell nicht geladen"} for tc in test_cases]

    X = vectorizer.transform(test_cases)
    predictions = model.predict(X)

    priority_mapping = {0: "niedrig", 1: "mittel", 2: "hoch"}
    return [{"test_case": test_cases[i], "priority": priority_mapping[predictions[i]]} for i in range(len(test_cases))]


# ** Funktion: Einfache Priorisierung von Testfällen**
def simple_prioritize_test_cases(test_cases, criteria_weights=None):
    """
    Eine einfache Heuristik zur Priorisierung von Testfällen.

    :param test_cases: Liste von Testfallbeschreibungen.
    :param criteria_weights: Gewichtungen für Kriterien (z. B. Risiko, Komplexität).
    :return: Sortierte Testfälle basierend auf Priorität.
    """
    if criteria_weights is None:
        criteria_weights = {"risk": 0.4, "complexity": 0.3, "impact": 0.3}

    priorities = []
    for test_case in test_cases:
        risk_score = len(test_case.split()) * criteria_weights["risk"]
        complexity_score = len(set(test_case.split())) * criteria_weights["complexity"]
        impact_score = len(test_case) * criteria_weights["impact"]
        total_score = risk_score + complexity_score + impact_score
        priorities.append({"test_case": test_case, "score": total_score})

    return sorted(priorities, key=lambda x: x["score"], reverse=True)


# ** Funktion: Sentimentanalyse**
def sentiment_analysis(text):
    """
    Analysiert die Stimmung eines Testfalls (positiv, neutral, negativ).

    :param text: Testfallbeschreibung.
    :return: Stimmung des Textes.
    """
    if "erfolgreich" in text or "bestanden" in text:
        return "positiv"
    elif "fehlgeschlagen" in text or "Fehler" in text:
        return "negativ"
    else:
        return "neutral"
