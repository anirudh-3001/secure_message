import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import API from '../services/api';
import {
  generateRSAKeyPair,
  exportPublicKey,
  exportPrivateKey,
  encryptPrivateKeyWithPassword,
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
      // Generate key pair
      const { publicKey, privateKey } = await generateRSAKeyPair();
      const exportedPublicKey = await exportPublicKey(publicKey);
      const exportedPrivateKey = await exportPrivateKey(privateKey);

      // Encrypt private key with password
      const encryptedPrivateKey = await encryptPrivateKeyWithPassword(exportedPrivateKey, password);

      // Send registration to backend
      await API.post('/api/auth/register', {
        name,
        email,
        password,
        public_key: exportedPublicKey,
        encrypted_private_key: encryptedPrivateKey,
      });

      navigate('/login');
    } catch (err) {
      setError(
        err.response?.data?.error ||
        err.response?.data?.message ||
        err.message ||
        'Registration failed'
      );
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
        <p>
          Already have an account? <Link to="/login">Login here</Link>
        </p>
      </form>
    </div>
  );
};

export default Register;