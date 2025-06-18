class User:
    """
    User model representing the schema for user data.
    """
    def __init__(self, email, password=None, role='user', 
                 public_key=None, encrypted_private_key=None, 
                 created_at=None, username=None):  # <-- added username
        self.email = email
        self.password = password  # Should be stored hashed in database
        self.role = role
        self.public_key = public_key
        self.encrypted_private_key = encrypted_private_key
        self.created_at = created_at
        self.username = username  # <-- added

    def to_dict(self):
        """Convert user object to dictionary for storage"""
        data = {
            'email': self.email,
            'role': self.role,
            'public_key': self.public_key,
            'encrypted_private_key': self.encrypted_private_key,
            'username': self.username  # <-- added
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
            created_at=data.get('created_at'),
            username=data.get('username')  # <-- added
        )

    def is_admin(self):
        return self.role == 'admin'

    def has_keys(self):
        return self.public_key is not None and self.encrypted_private_key is not None
