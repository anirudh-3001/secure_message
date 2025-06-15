# utils/encryption.py

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
import base64
import json


def encrypt_message(message, rsa_public_key_pem):
    """
    Encrypts a message using hybrid RSA + AES encryption.
    Returns base64 encoded payload.
    """
    # Generate a random AES session key
    session_key = get_random_bytes(16)

    # Encrypt the message with AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(message.encode())

    # Load recipient public key
    public_key = RSA.import_key(rsa_public_key_pem)
    cipher_rsa = PKCS1_OAEP.new(public_key)

    # Encrypt the AES session key with the public RSA key
    encrypted_session_key = cipher_rsa.encrypt(session_key)

    # Encode everything into base64 to make it JSON-friendly
    encrypted_payload = {
        'encrypted_session_key': base64.b64encode(encrypted_session_key).decode(),
        'nonce': base64.b64encode(cipher_aes.nonce).decode(),
        'tag': base64.b64encode(tag).decode(),
        'ciphertext': base64.b64encode(ciphertext).decode()
    }

    return json.dumps(encrypted_payload)


def decrypt_message(encrypted_payload_json, rsa_private_key_pem):
    """
    Decrypts a message encrypted with encrypt_message.
    Requires RSA private key.
    """
    encrypted_payload = json.loads(encrypted_payload_json)

    # Decode base64 components
    encrypted_session_key = base64.b64decode(encrypted_payload['encrypted_session_key'])
    nonce = base64.b64decode(encrypted_payload['nonce'])
    tag = base64.b64decode(encrypted_payload['tag'])
    ciphertext = base64.b64decode(encrypted_payload['ciphertext'])

    # Load RSA private key and decrypt AES session key
    private_key = RSA.import_key(rsa_private_key_pem)
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(encrypted_session_key)

    # Decrypt AES-encrypted message
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    message = cipher_aes.decrypt_and_verify(ciphertext, tag)

    return message.decode()
