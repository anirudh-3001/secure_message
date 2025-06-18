from flask import Blueprint, request, jsonify
from firebase_admin import auth
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.auth_service import register_user, login_user, get_all_users

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user.
    Expects JSON: { email, password, username, public_key, encrypted_private_key }
    """
    data = request.get_json()
    return register_user(data)

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Log in a user and return JWT.
    Expects JSON: { email, password }
    """
    data = request.get_json()
    return login_user(data)

@auth_bp.route("/users", methods=["GET"])
@jwt_required()
def users():
    return get_all_users()
