# app.py

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

    # Enable CORS (adjust origin for production)
    CORS(app, supports_credentials=True)

    # Initialize JWT
    jwt = JWTManager(app)

    # Initialize Firebase
    initialize_firebase()

    # Set up scheduled task for message cleanup
    scheduler = BackgroundScheduler()
    # Run cleanup every day at midnight
    scheduler.add_job(
        func=lambda: delete_expired_messages()[0],  # Extract just the result, not status code
        trigger='interval', 
        hours=12  # Run every 12 hours
    )
    scheduler.start()
    
    # Make sure scheduler shuts down properly when app exits
    atexit.register(lambda: scheduler.shutdown())

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")

    # Health Check
    @app.route("/")
    def index():
        return jsonify({"message": "Secure Messaging API is running."}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=app.config['DEBUG'])