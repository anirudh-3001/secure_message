# firebase_config.py

import firebase_admin
from firebase_admin import credentials, firestore, auth
from config import Config
import os
import base64
import tempfile

firebase_app = None
db = None


def initialize_firebase():
    global firebase_app, db

    if firebase_app:
        return firebase_app, db

    if Config.FIREBASE_CREDENTIAL_PATH and Config.FIREBASE_CREDENTIAL_PATH.endswith(".json"):
        cred = credentials.Certificate(Config.FIREBASE_CREDENTIAL_PATH)
    else:
        # Assume base64-encoded credentials (more secure in env)
        decoded = base64.b64decode(Config.FIREBASE_CREDENTIAL_PATH)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            tmp_file.write(decoded)
            tmp_file.flush()
            cred = credentials.Certificate(tmp_file.name)

    firebase_app = firebase_admin.initialize_app(cred, {
        'databaseURL': Config.FIREBASE_DB_URL
    })
    db = firestore.client()
    return firebase_app, db


def get_firestore():
    if not db:
        initialize_firebase()
    return db


def get_auth():
    if not firebase_app:
        initialize_firebase()
    return auth
