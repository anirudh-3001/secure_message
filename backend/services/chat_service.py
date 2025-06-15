# services/chat_service.py

from firebase_admin import firestore
from datetime import datetime, timedelta
import re
import time
from functools import wraps
from models.message import Message

db = firestore.client()

# Rate limiting configuration
MESSAGE_LIMITS = {}
MAX_MESSAGES = 10  # Maximum messages per time window
RATE_LIMIT_WINDOW = 60  # Time window in seconds (1 minute)
MAX_CONTENT_SIZE = 10 * 1024  # 10KB maximum message size

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def check_message_rate_limit(sender):
    """
    Check if user has exceeded message rate limit
    Returns (is_allowed, seconds_to_wait)
    """
    current_time = time.time()
    
    # Initialize or clean up old entries
    if sender not in MESSAGE_LIMITS:
        MESSAGE_LIMITS[sender] = []
    else:
        # Remove timestamps older than the window
        MESSAGE_LIMITS[sender] = [t for t in MESSAGE_LIMITS[sender] 
                                if current_time - t < RATE_LIMIT_WINDOW]
    
    # Check if user has exceeded limit
    if len(MESSAGE_LIMITS[sender]) >= MAX_MESSAGES:
        oldest = min(MESSAGE_LIMITS[sender])
        time_to_wait = int(RATE_LIMIT_WINDOW - (current_time - oldest))
        return False, time_to_wait
    
    return True, 0

def add_message_timestamp(sender):
    """Record a message send timestamp for rate limiting"""
    current_time = time.time()
    if sender not in MESSAGE_LIMITS:
        MESSAGE_LIMITS[sender] = []
    MESSAGE_LIMITS[sender].append(current_time)

def send_encrypted_message(data):
    """
    Stores an encrypted message in Firestore.
    Assumes message is already encrypted with receiver's public key.
    """
    try:
        # Input validation
        if not isinstance(data, dict):
            return {"error": "Invalid request format"}, 400
            
        sender = data.get('sender')
        receiver = data.get('receiver')
        encrypted_content = data.get('encrypted_content')
        expires_in_seconds = data.get('expires_in_seconds', 3600)
        
        # Validate required fields
        if not sender or not receiver or not encrypted_content:
            return {"error": "Missing required fields: sender, receiver, and encrypted_content"}, 400
            
        # Validate email formats
        if not validate_email(sender):
            return {"error": "Invalid sender email format"}, 400
            
        if not validate_email(receiver):
            return {"error": "Invalid receiver email format"}, 400
        
        # Validate content size
        if len(encrypted_content) > MAX_CONTENT_SIZE:
            return {"error": f"Message too large. Maximum size is {MAX_CONTENT_SIZE} bytes"}, 413
        
        # Validate expiration time
        if not isinstance(expires_in_seconds, (int, float)) or expires_in_seconds <= 0:
            return {"error": "Invalid expiration time"}, 400
            
        # Apply rate limiting
        allowed, wait_time = check_message_rate_limit(sender)
        if not allowed:
            return {
                "error": f"Rate limit exceeded. Try again in {wait_time} seconds", 
                "retry_after": wait_time
            }, 429

        # Check if receiver exists
        receiver_doc = db.collection('users').document(receiver).get()
        if not receiver_doc.exists:
            return {"error": "Recipient not found"}, 404

        current_time = datetime.utcnow()
        expires_at = current_time + timedelta(seconds=expires_in_seconds)

        # Create a message object using the Message model
        message = Message(
            sender=sender,
            receiver=receiver,
            encrypted_content=encrypted_content,
            timestamp=current_time.isoformat(),
            expires_at=expires_at.isoformat(),
            read=False
        )

        # Save the message to Firestore
        message_ref = db.collection('messages').document()
        message_ref.set(message.to_dict())
        
        # Update rate limiting data
        add_message_timestamp(sender)

        return {
            "message": "Message sent successfully", 
            "message_id": message_ref.id,
            "expires_at": expires_at.isoformat()
        }, 200
        
    except Exception as e:
        return {"error": f"Failed to send message: {str(e)}"}, 500

def get_received_messages(user_email):
    """
    Retrieves unexpired encrypted messages received by the user.
    """
    try:
        # Input validation
        if not user_email or not validate_email(user_email):
            return {"error": "Invalid email format"}, 400
            
        now = datetime.utcnow().isoformat()

        # Verify user exists
        user_doc = db.collection('users').document(user_email).get()
        if not user_doc.exists:
            return {"error": "User not found"}, 404

        messages_ref = db.collection('messages')\
            .where('receiver', '==', user_email)\
            .where('expires_at', '>', now)\
            .stream()

        messages = []
        for msg in messages_ref:
            # Create a Message object from the Firestore document
            message_data = msg.to_dict()
            message = Message.from_dict(message_data, message_id=msg.id)
            
            # Add to results
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

        return {"messages": messages, "count": len(messages)}, 200
        
    except Exception as e:
        return {"error": f"Failed to retrieve messages: {str(e)}"}, 500

def get_sent_messages(user_email):
    """
    Retrieves sent messages for auditing (if allowed by role).
    """
    try:
        # Input validation
        if not user_email or not validate_email(user_email):
            return {"error": "Invalid email format"}, 400
            
        # Verify user exists
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
            # Create a Message object from the Firestore document
            message_data = msg.to_dict()
            message = Message.from_dict(message_data, message_id=msg.id)
            
            # Add to results
            messages.append({
                "id": message.id,
                "receiver": message.receiver,
                "encrypted_content": message.encrypted_content,
                "timestamp": message.timestamp,
                "expires_at": message.expires_at,
                "read": message.read
            })

        return {"messages": messages, "count": len(messages)}, 200
        
    except Exception as e:
        return {"error": f"Failed to retrieve sent messages: {str(e)}"}, 500

def delete_expired_messages():
    """
    Manually or periodically called to clean up expired messages.
    Can be triggered via cron or admin-only route.
    """
    try:
        now = datetime.utcnow().isoformat()
        batch_size = 100  # Process in batches to avoid timeouts
        
        # Get expired messages
        expired = db.collection('messages').where('expires_at', '<=', now).limit(batch_size).stream()
        
        deleted = []
        batch = db.batch()
        count = 0
        
        for doc in expired:
            batch.delete(db.collection('messages').document(doc.id))
            deleted.append(doc.id)
            count += 1
            
            # Commit batch when it reaches the limit
            if count >= batch_size:
                batch.commit()
                batch = db.batch()
                count = 0
                
        # Commit any remaining deletions
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
    """
    Mark a message as read
    """
    try:
        if not message_id:
            return {"error": "Message ID is required"}, 400
            
        # Validate user
        if not user_email or not validate_email(user_email):
            return {"error": "Invalid user"}, 400
        
        # Get the message
        message_ref = db.collection('messages').document(message_id)
        message_doc = message_ref.get()
        
        if not message_doc.exists:
            return {"error": "Message not found"}, 404
            
        # Create a Message object from the document
        message_data = message_doc.to_dict()
        message = Message.from_dict(message_data, message_id=message_doc.id)
        
        # Check if user is the receiver of this message
        if message.receiver != user_email:
            return {"error": "Unauthorized access"}, 403
            
        # Check if message has expired
        if message.is_expired:
            return {"error": "Message has expired"}, 410
            
        # Mark as read
        message_ref.update({'read': True})
        
        return {"message": "Message marked as read"}, 200
        
    except Exception as e:
        return {"error": f"Failed to mark message as read: {str(e)}"}, 500