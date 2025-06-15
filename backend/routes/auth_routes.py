# routes/auth_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import auth_service

auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    Expects JSON: { email, password, public_key, encrypted_private_key }
    """
    data = request.get_json()
    return auth_service.register_user(data)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Logs in a user and returns JWT, public key, and encrypted private key.
    Expects JSON: { email, password }
    """
    data = request.get_json()
    return auth_service.login_user(data)


@auth_bp.route('/public_key/<email>', methods=['GET'])
@jwt_required()
def get_public_key(email):
    """
    Fetch another user's public key (for encrypting messages).
    """
    key = auth_service.get_user_public_key(email)
    if key:
        return jsonify({"public_key": key}), 200
    return jsonify({"error": "User not found"}), 404


@auth_bp.route('/me/encrypted_private_key', methods=['GET'])
@jwt_required()
def get_my_encrypted_private_key():
    """
    Returns the logged-in user's encrypted private key.
    """
    email = get_jwt_identity()
    key = auth_service.get_user_encrypted_private_key(email)
    if key:
        return jsonify({"encrypted_private_key": key}), 200
    return jsonify({"error": "Private key not found"}), 404
