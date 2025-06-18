from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from firebase_config import get_firestore
from services import chat_service, auth_service

chat_bp = Blueprint('chat', __name__, url_prefix="/api/chat")
db = get_firestore()

@chat_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    sender = get_jwt_identity()
    print("DEBUG: send_message called, sender =", sender)
    data = request.get_json()
    print("DEBUG: request data =", data)
    data['sender'] = sender
    response, status = chat_service.send_encrypted_message(data)
    print("DEBUG: send_encrypted_message returned", response, status)
    return jsonify(response), status

@chat_bp.route('/inbox', methods=['GET'])
@jwt_required()
def get_inbox():
    email = get_jwt_identity()
    print("DEBUG: get_inbox called, email =", email)
    messages, status = chat_service.get_received_messages(email)
    print("DEBUG: get_received_messages returned", messages, status)
    if isinstance(messages, dict) and "error" in messages:
        print("DEBUG: returning error", messages)
        return jsonify(messages), status
    print("DEBUG: returning messages", messages)
    return jsonify(messages), status

@chat_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent_messages():
    email = get_jwt_identity()
    print("DEBUG: get_sent_messages called, email =", email)
    role = auth_service.get_user_role(email)
    print("DEBUG: user role =", role)

    if role not in ['admin', 'user']:
        print("DEBUG: Unauthorized user")
        return jsonify({"error": "Unauthorized"}), 403

    messages, status = chat_service.get_sent_messages(email)
    print("DEBUG: get_sent_messages service returned", messages, status)
    if isinstance(messages, dict) and "error" in messages:
        print("DEBUG: returning error", messages)
        return jsonify(messages), status
    print("DEBUG: returning messages", messages)
    return jsonify(messages), status

@chat_bp.route('/cleanup', methods=['DELETE'])
@jwt_required()
def cleanup_expired_messages():
    email = get_jwt_identity()
    print("DEBUG: cleanup_expired_messages called, email =", email)
    role = auth_service.get_user_role(email)
    print("DEBUG: user role =", role)

    if role != 'admin':
        print("DEBUG: Non-admin tried to cleanup")
        return jsonify({"error": "Admin only"}), 403

    response, status = chat_service.delete_expired_messages()
    print("DEBUG: delete_expired_messages returned", response, status)
    return jsonify(response), status

@chat_bp.route('/read/<message_id>', methods=['POST'])
@jwt_required()
def mark_as_read(message_id):
    user = get_jwt_identity()
    print("DEBUG: mark_as_read called, message_id =", message_id, "user =", user)
    response, status = chat_service.mark_message_as_read(message_id, user)
    print("DEBUG: mark_message_as_read returned", response, status)
    return jsonify(response), status