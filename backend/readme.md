# Secure Messaging Backend

A Flask-based backend service for an end-to-end encrypted messaging platform with robust security features.

## Project Overview
This project implements a secure communication system where users can exchange messages that are protected by end-to-end encryption. Only the intended recipients can decrypt and read messages, ensuring privacy and confidentiality.

## Features
- **End-to-End Encryption**: Messages are encrypted on the sender's device and can only be decrypted by the recipient
- **User Authentication**: Secure login and registration system with password hashing
- **Key Management**: RSA key pair generation and secure storage of encrypted private keys
- **Message Expiration**: Automatic expiration and deletion of messages after a specified time
- **Rate Limiting**: Protection against brute force attacks and spam
- **Read Receipts**: Track when messages have been read

## Security Measures

### Authentication Security
- 🔒 Password Hashing: bcrypt with salt
- 🔑 Password Validation: 8+ chars, uppercase, lowercase, digits
- 🛡️ Brute Force Protection: 5 attempts → 5-minute lockout
- 🪙 JWT Authentication: 1-hour expiration tokens
- 👨‍💻 Role-Based Access Control: User/admin permissions

### Message Security
- 🏷️ Hybrid Encryption: RSA (2048-bit) + AES
- 🔐 Key Protection: Private keys encrypted with user's password
- 📏 Message Size Limits: Max 10KB to prevent DoS
- ⏱️ Rate Limiting: 10 messages/minute/user
- 🗑️ Message Expiration: Auto-deletion of expired messages
- 👁️ Authorization Checks: Users can only read their messages

### System Security
- ✅ Input Validation: All user inputs validated
- ❌ Error Handling: Structured responses (no sensitive data)
- 📝 Detailed Logging: Activity monitoring

## Installation

### Prerequisites
- Python 3.7+
- Firebase account with Firestore
- `pip`

### Setup Steps
# 1. Create and activate a virtual environment
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

# 2. Install required packages: `pip install -r requirements.txt`

# 3. Firebase Configuration
- Create a Firebase project at https://console.firebase.google.com/
- Generate a new private key from Project Settings > Service accounts > Generate new private key
- Save the JSON file to your project directory as firebase-adminsdk.json

# 4.Update environment variables

# 5.Run the application
  python app.py
  #The backend will be accessible at http://localhost:5000.

## API Endpoints
# Authentication
-POST /api/auth/register - Register a new user
-POST /api/auth/login - Authenticate and receive tokens
-GET /api/auth/public_key/{email} - Get a user's public key
-GET /api/auth/me/encrypted_private_key - Get your encrypted private key

# Messaging
-POST /api/chat/send - Send an encrypted message
-GET /api/chat/inbox - Get received messages
-GET /api/chat/sent - Get sent messages
-DELETE /api/chat/cleanup - Delete expired messages (admin only)

## Architecture

The application follows a modular architecture:

Models: Define data structures and validation rules

Services: Contain business logic and database operations

Routes: Handle HTTP requests and responses
Utils: Provide encryption and key management utilities

## Data Flow
# User Registration:

User generates an RSA key pair in the frontend
Private key is encrypted with the user's password
User information including public key and encrypted private key is sent to the server
Server stores user data in Firestore

# Sending a Message:

Sender retrieves recipient's public key
Message is encrypted using hybrid encryption
Encrypted message is sent to the server
Server validates and stores the message

# Receiving Messages:

User authenticates and requests inbox
Server returns encrypted messages
Client decrypts messages using the user's private key

# Firebase Collections
The application uses two Firestore collections:

1.users: Stores user information and encryption keys
2.messages: Stores encrypted messages with metadata

## Security Implementation Details
End-to-End Encryption Process
1.Key Generation: RSA key pair (2048-bit) generated during registration

2.Private Key Encryption:

-User's RSA private key is encrypted with AES-256
-AES key is derived from the user's password using PBKDF2 with 1,000,000 iterations
-Result is stored in JSON format with salt, nonce, and authentication tag

3.Message Encryption:

-Random AES session key generated for each message
-Message encrypted with AES in EAX mode
-Session key encrypted with recipient's RSA public key
-All components assembled into a JSON payload

# Rate Limiting Implementation
The system uses a sliding window approach for rate limiting:

1.For login: Tracks failed attempts with escalating lockout periods
2.For messaging: Limits users to 10 messages per minute