# SecureChat - End-to-End Encrypted Messaging

A secure messaging platform featuring military-grade encryption, ensuring your communications remain private and protected from unauthorized access. This application implements comprehensive security measures at every level.

## Features

### Security Features
- **End-to-End Encryption**: RSA-OAEP 2048-bit encryption ensures only intended recipients can read messages
- **Hybrid Encryption System**: Combines RSA with AES for optimal security and performance
- **Private Key Protection**: User private keys are encrypted with AES-GCM derived from password using PBKDF2 (100,000 iterations)
- **Password Security**: bcrypt hashing with salt for secure password storage
- **HTTP Security Headers**: Comprehensive protection against XSS, clickjacking, and other web vulnerabilities
- **Anti-Brute Force Measures**: Account lockout after 5 failed attempts
- **Message Expiration**: Automatic deletion of expired messages
- **Rate Limiting**: Protection against message flooding (10 messages per minute)

### User Features
- User registration and authentication
- Contact management
- Real-time encrypted messaging
- Message status indicators (read/unread)
- Auto-expiring messages

## Setup Instructions

### Prerequisites
- Node.js (v14 or higher)
- Python 3.7+ with pip
- Firebase account

### Frontend Setup
1. Navigate to the frontend directory:
   ```
   cd secure-message-frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

4. The application will be available at [http://localhost:3000](http://localhost:3000)

### Backend Setup
1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment:
   ```
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the backend directory with the following content:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret-key
   FIREBASE_CREDENTIAL_PATH=path/to/your/firebase-adminsdk.json
   FIREBASE_DB_URL=https://your-project-id.firebaseio.com
   ```

5. Firebase Setup:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Set up Firestore Database
   - Generate a new private key from Project Settings > Service accounts > Generate new private key
   - Save the JSON file in the backend directory as `firebase-adminsdk.json`

6. Start the backend server:
   ```
   python app.py
   ```

7. The API will be available at [http://localhost:5000](http://localhost:5000)

## How It Works

### Registration Process
1. When a user registers, the frontend generates an RSA key pair directly in the browser
2. The private key is encrypted using the user's password
3. The public key and encrypted private key are sent to the server along with user credentials
4. The server stores the public key and encrypted private key but can never access the actual private key

### Sending Messages
1. User selects a recipient from their contacts
2. The sender's browser retrieves the recipient's public key from the server
3. The message is encrypted in the browser using the recipient's public key
4. Only the encrypted message is sent to and stored on the server
5. The server cannot read the message content

### Receiving Messages
1. User logs in and retrieves their encrypted messages
2. The browser decrypts the user's private key using their password
3. Each message is decrypted using the user's private key
4. All decryption happens locally in the user's browser
5. The server never sees the decrypted content

## Security Architecture

### Frontend Security
- Content Security Policy (CSP) to prevent XSS attacks
- X-Frame-Options to prevent clickjacking
- X-Content-Type-Options to prevent MIME type sniffing
- Referrer-Policy to control information in HTTP headers
- Permissions-Policy to restrict browser features
- Secure cookie handling with SameSite and Secure flags
- Anti-fingerprinting measures to reduce identifiable information

### Backend Security
- JWT authentication with short-lived tokens (1 hour)
- Role-based access control for API endpoints
- Rate limiting on sensitive operations
- bcrypt for password hashing with high work factor
- Input validation and sanitization
- Secure HTTP headers
- Message size limits to prevent DoS attacks
- Automatic deletion of expired messages

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and receive JWT token
- `GET /api/auth/users` - Get available contacts
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/public_key/:email` - Get public key for a user

### Messaging
- `POST /api/chat/send` - Send an encrypted message
- `GET /api/chat/inbox` - Get received messages

## Best Practices for Users
1. Use strong, unique passwords
2. Don't share your password with anyone
3. Log out when using shared computers
4. Verify contacts before sending sensitive information
5. Be aware that messages will automatically expire after their set duration

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
