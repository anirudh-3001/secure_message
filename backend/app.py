from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from firebase_config import initialize_firebase
from services.chat_service import delete_expired_messages

from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp

def create_app():
    app = Flask(__name__)

    # Load config
    app.config['DEBUG'] = Config.DEBUG
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY

    # Enable CORS for both local and deployed frontend
    CORS(app, origins=[
        "http://localhost:3000",             # Local development
        "https://message-5f5d7.web.app"      # Your deployed frontend
    ], supports_credentials=True)

    # Initialize JWT
    jwt = JWTManager(app)

    # Initialize Firebase (must be called BEFORE any Firestore usage!)
    initialize_firebase()

    # Set up scheduled task for message cleanup
    scheduler = BackgroundScheduler()
    # Run cleanup every 12 hours
    scheduler.add_job(
        func=lambda: delete_expired_messages()[0],  # Extract just the result, not status code
        trigger='interval',
        hours=12
    )
    scheduler.start()

    # Make sure scheduler shuts down properly when app exits
    atexit.register(lambda: scheduler.shutdown())

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")

    # 🔐 Add security headers globally
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'none';"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    # Health Check
    @app.route("/")
    def index():
        return jsonify({"message": "Secure Messaging API is running."}), 200

    return app

# Expose app for WSGI servers like Gunicorn
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config['DEBUG'])
