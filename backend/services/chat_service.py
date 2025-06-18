from datetime import datetime, timedelta
import re
import time
from models.message import Message
from firebase_config import get_firestore

db = get_firestore()

MESSAGE_LIMITS = {}
MAX_MESSAGES = 10
RATE_LIMIT_WINDOW = 60  # seconds
MAX_CONTENT_SIZE = 10 * 1024  # 10KB

def validate_email(email):
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def check_message_rate_limit(sender):
    current_time = time.time()
    if sender not in MESSAGE_LIMITS:
        MESSAGE_LIMITS[sender] = []
    else:
        MESSAGE_LIMITS[sender] = [t for t in MESSAGE_LIMITS[sender] if current_time - t < RATE_LIMIT_WINDOW]
    if len(MESSAGE_LIMITS[sender]) >= MAX_MESSAGES:
        oldest = min(MESSAGE_LIMITS[sender])
        time_to_wait = int(RATE_LIMIT_WINDOW - (current_time - oldest))
        return False, time_to_wait
    return True, 0

def add_message_timestamp(sender):
    current_time = time.time()
    if sender not in MESSAGE_LIMITS:
        MESSAGE_LIMITS[sender] = []
    MESSAGE_LIMITS[sender].append(current_time)

def send_encrypted_message(data):
    try:
        if not isinstance(data, dict):
            return {"error": "Invalid request format"}, 400
        sender = data.get('sender')
        receiver = data.get('receiver')
        encrypted_content = data.get('encrypted_content')
        expires_in_seconds = data.get('expires_in_seconds', 3600)
        if not sender or not receiver or not encrypted_content:
            return {"error": "Missing required fields: sender, receiver, and encrypted_content"}, 400
        if not validate_email(sender):
            return {"error": "Invalid sender email format"}, 400
        if not validate_email(receiver):
            return {"error": "Invalid receiver email format"}, 400
        if len(encrypted_content) > MAX_CONTENT_SIZE:
            return {"error": f"Message too large. Maximum size is {MAX_CONTENT_SIZE} bytes"}, 413
        if not isinstance(expires_in_seconds, (int, float)) or expires_in_seconds <= 0:
            return {"error": "Invalid expiration time"}, 400
        allowed, wait_time = check_message_rate_limit(sender)
        if not allowed:
            return {
                "error": f"Rate limit exceeded. Try again in {wait_time} seconds",
                "retry_after": wait_time
            }, 429
        receiver_doc = db.collection('users').document(receiver).get()
        if not receiver_doc.exists:
            return {"error": "Recipient not found"}, 404
        current_time = datetime.utcnow()
        expires_at = current_time + timedelta(seconds=expires_in_seconds)
        message = Message(
            sender=sender,
            receiver=receiver,
            encrypted_content=encrypted_content,
            timestamp=current_time.isoformat(),
            expires_at=expires_at.isoformat(),
            read=False
        )
        message_ref = db.collection('messages').document()
        message_ref.set(message.to_dict())
        add_message_timestamp(sender)
        return {
            "message": "Message sent successfully",
            "message_id": message_ref.id,
            "expires_at": expires_at.isoformat()
        }, 200
    except Exception as e:
        return {"error": f"Failed to send message: {str(e)}"}, 500

def get_received_messages(user_email):
    try:
        if not user_email or not validate_email(user_email):
            return {"error": "Invalid email format"}, 400
        now = datetime.utcnow().isoformat()
        user_doc = db.collection('users').document(user_email).get()
        if not user_doc.exists:
            return {"error": "User not found"}, 404
        messages_ref = db.collection('messages')\
            .where('receiver', '==', user_email)\
            .where('expires_at', '>', now)\
            .stream()
        messages = []
        for msg in messages_ref:
            message_data = msg.to_dict()
            message = Message.from_dict(message_data, message_id=msg.id)
            messages.append({
                "id": message.id,
                "sender": message.sender,
                "encrypted_content": message.encrypted_content,
                "timestamp": message.timestamp,
                "expires_at": message.expires_at,
                "read": message.read
            })
            # Mark as read if not already
            if not message.read:
                db.collection('messages').document(msg.id).update({'read': True})
        return messages, 200
    except Exception as e:
        return {"error": f"Failed to retrieve messages: {str(e)}"}, 500

def get_sent_messages(user_email):
    try:
        if not user_email or not validate_email(user_email):
            return {"error": "Invalid email format"}, 400
        user_doc = db.collection('users').document(user_email).get()
        if not user_doc.exists:
            return {"error": "User not found"}, 404
        now = datetime.utcnow().isoformat()
        messages_ref = db.collection('messages')\
            .where('sender', '==', user_email)\
            .where('expires_at', '>', now)\
            .stream()
        messages = []
        for msg in messages_ref:
            message_data = msg.to_dict()
            message = Message.from_dict(message_data, message_id=msg.id)
            messages.append({
                "id": message.id,
                "receiver": message.receiver,
                "encrypted_content": message.encrypted_content,
                "timestamp": message.timestamp,
                "expires_at": message.expires_at,
                "read": message.read
            })
        return messages, 200
    except Exception as e:
        return {"error": f"Failed to retrieve sent messages: {str(e)}"}, 500

def delete_expired_messages():
    try:
        now = datetime.utcnow().isoformat()
        batch_size = 100
        expired = db.collection('messages').where('expires_at', '<=', now).limit(batch_size).stream()
        deleted = []
        batch = db.batch()
        count = 0
        for doc in expired:
            batch.delete(db.collection('messages').document(doc.id))
            deleted.append(doc.id)
            count += 1
            if count >= batch_size:
                batch.commit()
                batch = db.batch()
                count = 0
        if count > 0:
            batch.commit()
        return {
            "status": "success",
            "deleted_count": len(deleted),
            "message_ids": deleted if len(deleted) < 100 else f"{len(deleted)} messages deleted"
        }, 200
    except Exception as e:
        return {"error": f"Failed to delete expired messages: {str(e)}"}, 500

def mark_message_as_read(message_id, user_email):
    try:
        if not message_id:
            return {"error": "Message ID is required"}, 400
        if not user_email or not validate_email(user_email):
            return {"error": "Invalid user"}, 400
        message_ref = db.collection('messages').document(message_id)
        message_doc = message_ref.get()
        if not message_doc.exists:
            return {"error": "Message not found"}, 404
        message_data = message_doc.to_dict()
        message = Message.from_dict(message_data, message_id=message_doc.id)
        if message.receiver != user_email:
            return {"error": "Unauthorized access"}, 403
        if datetime.fromisoformat(message.expires_at) < datetime.utcnow():
            return {"error": "Message has expired"}, 410
        message_ref.update({'read': True})
        return {"message": "Message marked as read"}, 200
    except Exception as e:
        return {"error": f"Failed to mark message as read: {str(e)}"}, 500