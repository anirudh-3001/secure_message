import React, { useEffect, useState } from "react";
import API from "../services/api";

const Contacts = ({ onSelectUser }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get("/users")
      .then((res) => {
        setUsers(res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch users", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="contacts-container">
      <h2>Contacts</h2>
      <p>Invite: http://localhost:3000/register</p>
      {loading ? (
        <p>Loading users...</p>
      ) : users.length === 0 ? (
        <p>No contacts available</p>
      ) : (
        <ul>
          {users.map((user) => (
            <li key={user.email} onClick={() => onSelectUser(user)}>
              {user.email}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Contacts;