# message.py

from datetime import datetime

class Message:
    """
    Message model representing the schema for message data.
    Only contains data structure and validation rules - no database operations.
    """
    def __init__(self, sender, receiver, encrypted_content, 
                 timestamp=None, expires_at=None, read=False, message_id=None):
        self.id = message_id
        self.sender = sender
        self.receiver = receiver
        self.encrypted_content = encrypted_content
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.expires_at = expires_at
        self.read = read
        
    def to_dict(self):
        """Convert message object to dictionary for storage"""
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'encrypted_content': self.encrypted_content,
            'timestamp': self.timestamp,
            'expires_at': self.expires_at,
            'read': self.read
        }
        
    @staticmethod
    def from_dict(data, message_id=None):
        """Create message object from dictionary"""
        return Message(
            sender=data.get('sender'),
            receiver=data.get('receiver'),
            encrypted_content=data.get('encrypted_content'),
            timestamp=data.get('timestamp'),
            expires_at=data.get('expires_at'),
            read=data.get('read', False),
            message_id=message_id
        )
    
    @property
    def is_expired(self):
        """Check if message has expired"""
        if not self.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > expires
        except (ValueError, TypeError):
            return False