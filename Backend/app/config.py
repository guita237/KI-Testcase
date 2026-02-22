import os
from urllib.parse import quote

class Config:
    # fetch the DATABASE_URL from environment variables
    raw_db_url = os.getenv("DATABASE_URL")

    # Verify if the DATABASE_URL contains a password
    if raw_db_url and "@" in raw_db_url:
        # Extract the username and password from the DATABASE_URL
        parts = raw_db_url.split("@")
        first_part = parts[0].split("://")[1]
        username, password = first_part.split(":")
        encoded_password = quote(password)
        raw_db_url = raw_db_url.replace(f"{username}:{password}", f"{username}:{encoded_password}")

    # Set the SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI = raw_db_url.replace("postgresql://", "postgresql+psycopg2://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
