# config.py

import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

class Config:
    DEBUG = os.getenv("DEBUG", "False") == "True"
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret")

    # Firebase Admin SDK credentials path or base64
    FIREBASE_CREDENTIAL_PATH = os.getenv("FIREBASE_CREDENTIAL_PATH")
    FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
