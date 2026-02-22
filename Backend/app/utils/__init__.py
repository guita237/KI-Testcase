from .firebase import initialize_firebase, verify_token
from .sendmail import send_verification_email, send_reset_password, send_modification_email
from .nlp_utils import (
    generate_test_cases,
    generate_summary,
    find_redundant_test_cases,
    classify_requirements,
    classify_multiple_requirements,
    prioritize_test_cases,
    generate_test_script,
    parse_test_cases,
    generiere_testfälle,
    load_rag_files
)

from .ml_utils import (
    train_and_save_model,
    predict_category,
    simple_prioritize_test_cases,
    sentiment_analysis,
    find_redundant_tests_ml,
    prioritize_test_cases_with_ml
)

from .datei_typ import (
      extract_text_from_pdf,
      extract_text_from_docx,
      extract_text_from_xlsx
)

# Initialisieren Sie Firebase beim Laden des Moduls
initialize_firebase()

__all__ = ['send_verification_email', 'send_reset_password', 'send_modification_email']