import React, { useState, useEffect } from "react";
import API from "../services/api";
import {
  importPublicKey,
  importPrivateKey,
  encryptWithPublicKey,
  decryptWithPrivateKey,
  decryptPrivateKeyWithPassword
} from "../utils/crypto";
import { useNavigate } from "react-router-dom";
import { FaPaperPlane, FaUserFriends, FaUserCircle } from "react-icons/fa";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./Chat.css";

function Chat() {
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [plainText, setPlainText] = useState("");
  const [decryptedMessages, setDecryptedMessages] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchInbox();
    fetchUsers();
  }, []);

  useEffect(() => {
    if (messages.length > 0) decryptInboxMessages();
  }, [messages]);

  const fetchUsers = async () => {
    try {
      const res = await API.get("/api/auth/users", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      setUsers(res.data);
    } catch {
      toast.error("Failed to load users");
    }
  };

  const fetchInbox = async () => {
    try {
      const res = await API.get("/inbox");
      setMessages(res.data);
    } catch (err) {
      if (err.response?.status === 401) navigate("/");
      else toast.error("Failed to fetch messages.");
    }
  };

  const decryptInboxMessages = async () => {
    try {
      const encryptedPrivateKey = localStorage.getItem("encryptedPrivateKey");
      const password = localStorage.getItem("userPassword");
      const privateKeyBase64 = await decryptPrivateKeyWithPassword(
        encryptedPrivateKey,
        password
      );
      const privateKey = await importPrivateKey(privateKeyBase64);

      const decrypted = await Promise.all(
        messages.map(async (msg) => {
          try {
            const plaintext = await decryptWithPrivateKey(
              msg.encrypted_content,
              privateKey
            );
            return { ...msg, plaintext };
          } catch {
            return { ...msg, plaintext: "[Decryption failed]" };
          }
        })
      );
      setDecryptedMessages(decrypted);
    } catch {
      toast.error("Failed to decrypt messages.");
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!selectedUser || !plainText) {
      toast.error("Recipient and message are required.");
      return;
    }
    try {
      const keyRes = await API.get(`/public_key/${selectedUser}`);
      const recipientPublicKey = await importPublicKey(keyRes.data.public_key);
      const encryptedContent = await encryptWithPublicKey(plainText, recipientPublicKey);

      await API.post("/send", {
        receiver: selectedUser,
        encrypted_content: encryptedContent
      });
      toast.success("Message sent successfully");
      setPlainText("");
      fetchInbox();
    } catch (err) {
      toast.error(err.response?.data?.error || err.message || "Failed to send message.");
    }
  };

  return (
    <>
      <ToastContainer position="top-right" autoClose={3000} />
      <div className="chat-layout">
        <div className="chat-sidebar">
          <h3>Contacts</h3>
          <ul>
            {users.map((user) => (
              <li
                key={user.email}
                className={selectedUser === user.email ? "active" : ""}
                onClick={() => setSelectedUser(user.email)}
              >
                <FaUserCircle /> {user.username || user.email}
              </li>
            ))}
          </ul>
          <div className="chat-invite">
            <FaUserFriends /> Invite: <br />
            <small>{`${window.location.origin}/register`}</small>
          </div>
        </div>
        <div className="chat-main">
          <div className="chat-header">
            <FaUserCircle size={24} /> {selectedUser || "Select a user to chat"}
          </div>
          <div className="chat-messages">
            {decryptedMessages
              .filter((msg) => msg.sender === selectedUser)
              .map((msg, idx) => (
                <div key={idx} className="chat-message">
                  <div className="chat-meta">
                    <strong>From:</strong> {msg.sender} <br />
                    <small>{new Date(msg.timestamp).toLocaleString()}</small>
                  </div>
                  <div className="chat-decrypted">{msg.plaintext}</div>
                </div>
              ))}
          </div>
          {selectedUser && (
            <form onSubmit={handleSend} className="chat-form">
              <input
                value={plainText}
                onChange={(e) => setPlainText(e.target.value)}
                placeholder="Type your message"
                required
              />
              <button type="submit">
                <FaPaperPlane /> Send
              </button>
            </form>
          )}
        </div>
      </div>
    </>
  );
}

export default Chat;
