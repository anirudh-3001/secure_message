from flask import Blueprint, request, jsonify
from firebase_admin import auth, firestore
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.auth_service import register_user, login_user, get_all_users, get_user_by_email

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

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Get current user's info (including encrypted_private_key).
    """
    email = get_jwt_identity()
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "email": user.email,
        "username": getattr(user, "username", None),
        "encrypted_private_key": user.encrypted_private_key,
        "public_key": user.public_key,
    }), 200

# ---- ADD THIS ENDPOINT FOR PUBLIC KEY LOOKUP ----
@auth_bp.route("/public_key/<email>", methods=["GET"])
def get_public_key(email):
    """
    Get public key for a given email.
    """
    db = firestore.client()
    doc = db.collection("users").document(email).get()
    if not doc.exists:
        return jsonify({"error": "User not found"}), 404
    user_data = doc.to_dict()
    return jsonify({"public_key": user_data.get("public_key")}), 200