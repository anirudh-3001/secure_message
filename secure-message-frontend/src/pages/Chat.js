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
  const [loading, setLoading] = useState(true);
  const [privateKey, setPrivateKey] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      navigate("/login");
      return;
    }
    fetchUsers();
    fetchInbox();
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (messages.length > 0 && privateKey) {
      decryptInboxMessages();
    }
    // eslint-disable-next-line
  }, [messages, privateKey]);

  useEffect(() => {
    const loadPrivateKey = async () => {
      try {
        let encryptedPrivateKey =
          localStorage.getItem("encryptedPrivateKey") ||
          (await fetchAndStoreEncryptedPrivateKey());
        let password = localStorage.getItem("userPassword");
        if (!password) {
          password = prompt("Enter your password to decrypt your private key:");
          if (!password) {
            toast.error("Password required to decrypt your private key.");
            navigate("/login");
            return;
          }
          localStorage.setItem("userPassword", password);
        }
        const privateKeyBase64 = await decryptPrivateKeyWithPassword(
          encryptedPrivateKey,
          password
        );
        const pk = await importPrivateKey(privateKeyBase64);
        setPrivateKey(pk);
      } catch (err) {
        console.error(err);
        toast.error("Failed to decrypt your private key. Please log in again.");
        handleLogout();
      }
    };

    loadPrivateKey();
    // eslint-disable-next-line
  }, []);

  const fetchAndStoreEncryptedPrivateKey = async () => {
    try {
      const res = await API.get("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      const encryptedKey = res.data.encrypted_private_key;
      localStorage.setItem("encryptedPrivateKey", encryptedKey);
      return encryptedKey;
    } catch (err) {
      toast.error("Failed to retrieve your private key.");
      handleLogout();
      throw err;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("encryptedPrivateKey");
    localStorage.removeItem("userPassword");
    navigate("/login");
  };

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
    setLoading(true);
    try {
      const res = await API.get("/api/chat/inbox", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      setMessages(res.data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      if (err.response?.status === 401) handleLogout();
      else toast.error("Failed to fetch messages.");
    }
  };

  const decryptInboxMessages = async () => {
    try {
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
      const keyRes = await API.get(`/api/auth/public_key/${selectedUser}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      const recipientPublicKey = await importPublicKey(keyRes.data.public_key);
      const encryptedContent = await encryptWithPublicKey(plainText, recipientPublicKey);

      await API.post(
        "/api/chat/send",
        {
          receiver: selectedUser,
          encrypted_content: encryptedContent,
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      toast.success("Message sent successfully");
      setPlainText("");
      fetchInbox();
    } catch (err) {
      toast.error(err.response?.data?.error || err.message || "Failed to send message.");
    }
  };

  const filteredMessages = decryptedMessages.filter(
    (msg) =>
      (msg.sender === selectedUser && msg.receiver !== msg.sender) ||
      (msg.receiver === selectedUser && msg.sender !== msg.receiver)
  );

  return (
    <>
      <ToastContainer position="top-right" autoClose={3000} />
      <div className="chat-layout">
        <div className="chat-sidebar">
          <div className="logout-btn" style={{ marginBottom: 20 }}>
            <button onClick={handleLogout}>Logout</button>
          </div>
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
            {loading && <div>Loading messages...</div>}
            {!loading && !filteredMessages.length && (
              <div>No messages to display.</div>
            )}
            {filteredMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`chat-message ${msg.sender === selectedUser ? "from-them" : "from-me"}`}
              >
                <div className="chat-meta">
                  <strong>{msg.sender === selectedUser ? "From" : "To"}:</strong>{" "}
                  {msg.sender === selectedUser ? msg.sender : msg.receiver} <br />
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