import firebase_admin
from firebase_admin import credentials, firestore, auth
from config import Config
import base64
import tempfile

firebase_app = None
db = None

def initialize_firebase():
    global firebase_app, db

    # Defensive check: Only raise when initialization is requested
    if not Config.FIREBASE_CREDENTIAL_PATH:
        raise ValueError("FIREBASE_CREDENTIAL_PATH is not set. Please set it in your .env file or as an environment variable.")

    if firebase_app and db:
        # Already initialized
        return firebase_app, db

    if Config.FIREBASE_CREDENTIAL_PATH.endswith(".json"):
        cred = credentials.Certificate(Config.FIREBASE_CREDENTIAL_PATH)
    else:
        # Assume base64-encoded credentials (e.g. from env variable)
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
    global db
    if db is None:
        initialize_firebase()
    return db

def get_auth():
    global firebase_app
    if firebase_app is None:
        initialize_firebase()
    return auth