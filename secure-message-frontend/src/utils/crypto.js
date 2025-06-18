// Helper: Convert ArrayBuffer to Base64
export function arrayBufferToBase64(buffer) {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)));
}

// Helper: Convert Base64 to ArrayBuffer
export function base64ToArrayBuffer(base64) {
  const binary = atob(base64);
  return Uint8Array.from([...binary].map(char => char.charCodeAt(0))).buffer;
}

// Generate RSA-OAEP key pair
export async function generateRSAKeyPair() {
  const keyPair = await window.crypto.subtle.generateKey(
    {
      name: "RSA-OAEP",
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: "SHA-256",
    },
    true,
    ["encrypt", "decrypt"]
  );
  return keyPair;
}

// Export Public Key to Base64
export async function exportPublicKey(key) {
  const spki = await window.crypto.subtle.exportKey("spki", key);
  return arrayBufferToBase64(spki);
}

// Export Private Key to Base64
export async function exportPrivateKey(key) {
  const pkcs8 = await window.crypto.subtle.exportKey("pkcs8", key);
  return arrayBufferToBase64(pkcs8);
}

// Import Public Key from Base64
export async function importPublicKey(base64) {
  return window.crypto.subtle.importKey(
    "spki",
    base64ToArrayBuffer(base64),
    { name: "RSA-OAEP", hash: "SHA-256" },
    true,
    ["encrypt"]
  );
}

// Import Private Key from Base64
export async function importPrivateKey(base64) {
  return window.crypto.subtle.importKey(
    "pkcs8",
    base64ToArrayBuffer(base64),
    { name: "RSA-OAEP", hash: "SHA-256" },
    true,
    ["decrypt"]
  );
}

// Encrypt data with RSA public key (string input/output)
export async function encryptWithPublicKey(plainText, publicKey) {
  const enc = new TextEncoder();
  const data = enc.encode(plainText);
  const encrypted = await window.crypto.subtle.encrypt(
    { name: "RSA-OAEP" },
    publicKey,
    data
  );
  return arrayBufferToBase64(encrypted);
}

// Decrypt data with RSA private key (string input/output)
export async function decryptWithPrivateKey(cipherTextBase64, privateKey) {
  const encrypted = base64ToArrayBuffer(cipherTextBase64);
  const decrypted = await window.crypto.subtle.decrypt(
    { name: "RSA-OAEP" },
    privateKey,
    encrypted
  );
  const dec = new TextDecoder();
  return dec.decode(decrypted);
}

// Encrypt private key with password using AES-GCM
export async function encryptPrivateKeyWithPassword(privateKeyBase64, password) {
  const enc = new TextEncoder();
  const keyMaterial = await window.crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    { name: "PBKDF2" },
    false,
    ["deriveKey"]
  );
  const salt = window.crypto.getRandomValues(new Uint8Array(16));
  const derivedKey = await window.crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt,
      iterations: 100000,
      hash: "SHA-256"
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    true,
    ["encrypt", "decrypt"]
  );
  const iv = window.crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await window.crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    derivedKey,
    base64ToArrayBuffer(privateKeyBase64)
  );
  // Concatenate salt+iv+ciphertext (all base64) for storage
  return [
    arrayBufferToBase64(salt),
    arrayBufferToBase64(iv),
    arrayBufferToBase64(ciphertext)
  ].join(".");
}

// Decrypt private key with password using AES-GCM
export async function decryptPrivateKeyWithPassword(encrypted, password) {
  const [saltB64, ivB64, ciphertextB64] = encrypted.split(".");
  const enc = new TextEncoder();
  const keyMaterial = await window.crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    { name: "PBKDF2" },
    false,
    ["deriveKey"]
  );
  const salt = base64ToArrayBuffer(saltB64);
  const iv = base64ToArrayBuffer(ivB64);
  const derivedKey = await window.crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: salt,
      iterations: 100000,
      hash: "SHA-256"
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    true,
    ["encrypt", "decrypt"]
  );
  const decrypted = await window.crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    derivedKey,
    base64ToArrayBuffer(ciphertextB64)
  );
  return arrayBufferToBase64(decrypted); // This is the original private key in base64
}