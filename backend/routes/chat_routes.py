# routes/chat_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from firebase_config import get_firestore
from services import chat_service, auth_service

chat_bp = Blueprint('chat_bp', __name__)
db = get_firestore()

@chat_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    sender = get_jwt_identity()
    data = request.get_json()
    data['sender'] = sender
    return chat_service.send_encrypted_message(data)

@chat_bp.route('/inbox', methods=['GET'])
@jwt_required()
def get_inbox():
    email = get_jwt_identity()
    messages = chat_service.get_received_messages(email)
    return jsonify(messages), 200

@chat_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent_messages():
    email = get_jwt_identity()
    role = auth_service.get_user_role(email)

    if role not in ['admin', 'user']:
        return jsonify({"error": "Unauthorized"}), 403

    messages = chat_service.get_sent_messages(email)
    return jsonify(messages), 200

@chat_bp.route('/cleanup', methods=['DELETE'])
@jwt_required()
def cleanup_expired_messages():
    email = get_jwt_identity()
    role = auth_service.get_user_role(email)

    if role != 'admin':
        return jsonify({"error": "Admin only"}), 403

    return chat_service.delete_expired_messages()

@chat_bp.route('/read/<message_id>', methods=['POST'])
@jwt_required()
def mark_as_read(message_id):
    user = get_jwt_identity()
    return chat_service.mark_message_as_read(message_id, user)
