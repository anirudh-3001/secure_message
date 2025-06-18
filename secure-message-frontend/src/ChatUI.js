import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import {
  generateRSAKeyPair,
  exportPublicKey,
  exportPrivateKey,
  encryptPrivateKeyWithPassword,
} from "../utils/crypto";
import "./Auth.css"; // Include a stylish new CSS file

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const res = await API.post("/login", { email, password });
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("publicKey", res.data.public_key);
      localStorage.setItem("encryptedPrivateKey", res.data.encrypted_private_key);
      localStorage.setItem("userEmail", email);
      localStorage.setItem("userPassword", password);
      navigate("/chat");
    } catch (err) {
      setError(err.response?.data?.error || "Login failed.");
    }
  };

  return (
    <div className="auth-container">
      <form className="auth-form" onSubmit={handleLogin}>
        <h2>Welcome Back 👋</h2>
        <p className="subtext">Log in to your secure chat account</p>
        {error && <div className="error-msg">{error}</div>}
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" required />
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" required />
        <button type="submit">Login</button>
        <div className="divider">or</div>
        <div className="social-login">
          <button className="google-btn">Login with Google</button>
          <button className="github-btn">Login with GitHub</button>
        </div>
        <div className="footer-text">
          Don't have an account? <a href="/register">Sign up</a>
        </div>
      </form>
    </div>
  );
}

export function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setGenerating(true);
    try {
      const { publicKey, privateKey } = await generateRSAKeyPair();
      const publicKeyB64 = await exportPublicKey(publicKey);
      const privateKeyB64 = await exportPrivateKey(privateKey);
      const encryptedPrivateKey = await encryptPrivateKeyWithPassword(privateKeyB64, password);
      await API.post("/register", {
        email,
        password,
        public_key: publicKeyB64,
        encrypted_private_key: encryptedPrivateKey,
      });
      setSuccess("Registration successful! Redirecting to login...");
      setTimeout(() => navigate("/"), 1500);
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Registration failed. Try again.");
    }
    setGenerating(false);
  };

  return (
    <div className="auth-container">
      <form className="auth-form" onSubmit={handleRegister}>
        <h2>Create Account ✨</h2>
        <p className="subtext">Join the secure chat revolution</p>
        {error && <div className="error-msg">{error}</div>}
        {success && <div className="success-msg">{success}</div>}
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" required />
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" required />
        <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="Confirm Password" required />
        <button type="submit" disabled={generating}>{generating ? "Generating Keys..." : "Register"}</button>
        <div className="footer-text">
          Already have an account? <a href="/">Login</a>
        </div>
      </form>
    </div>
  );
}
