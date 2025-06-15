# user.py

class User:
    """
    User model representing the schema for user data.
    Only contains data structure and validation rules - no database operations.
    """
    def __init__(self, email, password=None, role='user', 
                 public_key=None, encrypted_private_key=None, created_at=None):
        self.email = email
        self.password = password  # Should be stored hashed in database
        self.role = role
        self.public_key = public_key
        self.encrypted_private_key = encrypted_private_key
        self.created_at = created_at
        
    def to_dict(self):
        """Convert user object to dictionary for storage"""
        data = {
            'email': self.email,
            'role': self.role,
            'public_key': self.public_key,
            'encrypted_private_key': self.encrypted_private_key
        }
        
        if self.password:
            data['password'] = self.password
            
        if self.created_at:
            data['created_at'] = self.created_at
            
        return data
        
    @staticmethod
    def from_dict(data):
        """Create user object from dictionary"""
        return User(
            email=data.get('email'),
            password=data.get('password'),
            role=data.get('role', 'user'),
            public_key=data.get('public_key'),
            encrypted_private_key=data.get('encrypted_private_key'),
            created_at=data.get('created_at')
        )
        
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
        
    def has_keys(self):
        """Check if user has encryption keys"""
        return self.public_key is not None and self.encrypted_private_key is not None