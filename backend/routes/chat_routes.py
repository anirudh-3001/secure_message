# routes/chat_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import chat_service
from services import auth_service

chat_bp = Blueprint('chat_bp', __name__)


@chat_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    """
    Send an encrypted message.
    Expects JSON: {
        receiver: str,
        encrypted_content: str,
        expires_in_seconds: int (optional, default: 3600)
    }
    """
    sender = get_jwt_identity()
    data = request.get_json()
    data['sender'] = sender
    return chat_service.send_encrypted_message(data)


@chat_bp.route('/inbox', methods=['GET'])
@jwt_required()
def get_inbox():
    """
    Retrieve all non-expired encrypted messages for the user.
    """
    email = get_jwt_identity()
    messages = chat_service.get_received_messages(email)
    return jsonify(messages), 200


@chat_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent_messages():
    """
    Retrieve all non-expired messages sent by the user.
    """
    email = get_jwt_identity()
    role = auth_service.get_user_role(email)

    if role != 'admin' and role != 'user':
        return jsonify({"error": "Unauthorized"}), 403

    messages = chat_service.get_sent_messages(email)
    return jsonify(messages), 200


@chat_bp.route('/cleanup', methods=['DELETE'])
@jwt_required()
def cleanup_expired_messages():
    """
    Deletes expired messages. Only allowed for admins.
    """
    email = get_jwt_identity()
    role = auth_service.get_user_role(email)

    if role != 'admin':
        return jsonify({"error": "Admin only"}), 403

    return chat_service.delete_expired_messages()
