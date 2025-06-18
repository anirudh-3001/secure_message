from flask_jwt_extended import create_access_token
from firebase_admin import firestore
import bcrypt
import re
import time
from datetime import timedelta
from functools import wraps
from models.user import User

db = firestore.client()

# For rate limiting
LOGIN_ATTEMPTS = {}
MAX_ATTEMPTS = 5
LOCKOUT_TIME = 300  # seconds (5 minutes)

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 8:
        return False
    # Check for at least one uppercase, lowercase, and digit
    if not (any(c.isupper() for c in password) and 
            any(c.islower() for c in password) and 
            any(c.isdigit() for c in password)):
        return False
    return True

def check_rate_limit(email):
    """Check if user is rate limited"""
    current_time = time.time()
    if email in LOGIN_ATTEMPTS:
        attempts, lockout_until = LOGIN_ATTEMPTS[email]
        
        # Check if user is in lockout period
        if lockout_until and current_time < lockout_until:
            return False, int(lockout_until - current_time)
        
        # Reset attempts if lockout period expired
        if lockout_until and current_time >= lockout_until:
            LOGIN_ATTEMPTS[email] = (0, None)
            
    return True, 0

def update_login_attempts(email, success):
    """Update login attempts counter"""
    current_time = time.time()
    if success:
        if email in LOGIN_ATTEMPTS:
            LOGIN_ATTEMPTS[email] = (0, None)
        return
        
    if email not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[email] = (1, None)
    else:
        attempts, _ = LOGIN_ATTEMPTS[email]
        attempts += 1
        
        if attempts >= MAX_ATTEMPTS:
            # Set lockout time
            LOGIN_ATTEMPTS[email] = (attempts, current_time + LOCKOUT_TIME)
        else:
            LOGIN_ATTEMPTS[email] = (attempts, None)

def register_user(data):
    """
    Registers a new user with email, password, public_key, encrypted_private_key, and username.
    """
    try:
        # Validate required fields
        required_fields = ['email', 'password', 'public_key', 'encrypted_private_key']
        for field in required_fields:
            if not data.get(field):
                return {"error": f"Missing required field: {field}"}, 400
        
        email = data.get('email')
        password = data.get('password')
        public_key = data.get('public_key')
        encrypted_private_key = data.get('encrypted_private_key')
        role = data.get('role', 'user')
        username = data.get('username')  # <-- NEW

        # Validate email format
        if not validate_email(email):
            return {"error": "Invalid email format"}, 400
            
        # Validate password strength
        if not validate_password(password):
            return {"error": "Password must be at least 8 characters with uppercase, lowercase, and digits"}, 400

        user_ref = db.collection('users').document(email)

        if user_ref.get().exists:
            return {"error": "User already exists"}, 409

        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Create a User object
        user = User(
            email=email,
            password=hashed_pw,
            role=role,
            public_key=public_key,
            encrypted_private_key=encrypted_private_key,
            username=username  # <-- NEW
        )

        # Save to Firestore
        user_ref = db.collection('users').document(email)
        user_dict = user.to_dict()
        user_dict['created_at'] = firestore.SERVER_TIMESTAMP  # Add timestamp
        user_ref.set(user_dict)

        return {"message": "User registered successfully"}, 201
    except Exception as e:
        return {"error": f"Registration failed: {str(e)}"}, 500

def login_user(data):
    """
    Logs in a user and returns JWT token + public key.
    """
    try:
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return {"error": "Email and password are required"}, 400
            
        email = data.get('email')
        password = data.get('password')
        
        # Check rate limiting
        allowed, wait_time = check_rate_limit(email)
        if not allowed:
            return {"error": f"Too many failed attempts. Try again in {wait_time} seconds"}, 429

        user_doc = db.collection('users').document(email).get()

        if not user_doc.exists:
            update_login_attempts(email, False)
            return {"error": "Invalid email or password"}, 401

        # Create User object from Firestore document
        user_data = user_doc.to_dict()
        user = User.from_dict(user_data)

        if not bcrypt.checkpw(password.encode(), user_data['password'].encode()):
            update_login_attempts(email, False)
            return {"error": "Invalid email or password"}, 401
            
        # Reset failed login attempts
        update_login_attempts(email, True)

        # Set token expiration time (e.g., 1 hour)
        expires = timedelta(hours=1)
        access_token = create_access_token(
            identity=email,
            expires_delta=expires,
            additional_claims={"role": user.role}
        )

        return {
            "access_token": access_token,
            "expires_in": 3600,  # seconds (1 hour)
            "role": user.role,
            "public_key": user.public_key,
            "encrypted_private_key": user.encrypted_private_key,
            "username": user.username  # <-- OPTIONAL
        }, 200
    except Exception as e:
        return {"error": f"Login failed: {str(e)}"}, 500

def get_user_role(email):
    """Get user role for authorization checks"""
    try:
        if not email:
            return None
            
        doc = db.collection("users").document(email).get()
        if doc.exists:
            user = User.from_dict(doc.to_dict())
            return user.role
        return None
    except Exception as e:
        print(f"Error getting user role: {str(e)}")
        return None

def get_user_public_key(email):
    """Get a user's public key for encrypting messages to them"""
    try:
        if not email:
            return None
            
        doc = db.collection("users").document(email).get()
        if doc.exists:
            user = User.from_dict(doc.to_dict())
            return user.public_key
        return None
    except Exception as e:
        print(f"Error getting public key: {str(e)}")
        return None

def get_user_encrypted_private_key(email):
    """Get a user's encrypted private key (for their own use only)"""
    try:
        if not email:
            return None
            
        doc = db.collection("users").document(email).get()
        if doc.exists:
            user = User.from_dict(doc.to_dict())
            return user.encrypted_private_key
        return None
    except Exception as e:
        print(f"Error getting encrypted private key: {str(e)}")
        return None

def get_all_users(exclude_email=None):
    """Return a list of users excluding the current one."""
    try:
        users_ref = db.collection("users")
        all_users = users_ref.stream()

        result = []
        for doc in all_users:
            user_data = doc.to_dict()
            if user_data["email"] != exclude_email:
                result.append({
                    "email": user_data["email"],
                    "username": user_data.get("username", "")  # optional fallback
                })
        return result
    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        return []
