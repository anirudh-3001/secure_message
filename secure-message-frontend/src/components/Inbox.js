import React, { useEffect, useState } from "react";
import API from "../services/api";

const Inbox = () => {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    API.get("/api/chat/inbox")
      .then((response) => {
        setMessages(response.data);
        setError("");
      })
      .catch((err) => {
        setError(
          err.response?.data?.msg ||
          err.response?.data?.error ||
          "Failed to load inbox."
        );
      });
  }, []);

  return (
    <div>
      <h2>Your Inbox</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      <ul>
        {messages.length === 0 && !error && <li>No messages found.</li>}
        {messages.map((msg, idx) => (
          <li key={msg.id || idx}>
            <strong>From:</strong> {msg.sender} <br />
            <strong>Message:</strong> {msg.content}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Inbox;