import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createUserWithEmailAndPassword, updateProfile } from 'firebase/auth';
import { auth } from '../firebase';
import {
  generateRSAKeyPair,
  exportPublicKey,
  exportPrivateKey,
  encryptPrivateKeyWithPassword
} from '../utils/crypto';
import './Auth.css';

const Register = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();

    try {
      // Firebase user creation
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;

      // Generate RSA key pair
      const { publicKey, privateKey } = await generateRSAKeyPair();

      // Export keys to base64
      const exportedPublicKey = await exportPublicKey(publicKey);
      const exportedPrivateKey = await exportPrivateKey(privateKey);

      // Encrypt private key with user's password
      const encryptedPrivateKey = await encryptPrivateKeyWithPassword(exportedPrivateKey, password);

      // Store keys in Firestore or your backend (to be implemented)

      // Set display name
      await updateProfile(user, { displayName: name });

      // Navigate to chat or login
      navigate('/login');
    } catch (err) {
      console.error(err);
      setError(err.message || 'Registration failed');
    }
  };

  return (
    <div className="auth-container">
      <h2>Register</h2>
      <form onSubmit={handleRegister} className="auth-form">
        <input
          type="text"
          placeholder="Name"
          value={name}
          required
          onChange={(e) => setName(e.target.value)}
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          required
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          required
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Register</button>
        {error && <p className="error">{error}</p>}
      </form>
    </div>
  );
  createUserWithEmailAndPassword(auth, email, password)

};

export default Register;
