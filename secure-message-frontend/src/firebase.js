import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyAGTeUoCiTJaJyhjdT3cogqxtAvvUKxfRM",
  authDomain: "message-5f5d7.firebaseapp.com",
  projectId: "message-5f5d7",
  storageBucket: "message-5f5d7.appspot.com",
  messagingSenderId: "682658967299",
  appId: "1:682658967299:web:39f17e600b1d24e44e4336",
  measurementId: "G-YJCMLHCSTQ"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);