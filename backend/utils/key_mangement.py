# utils/key_management.py

from Crypto.PublicKey import RSA
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import json


def generate_rsa_key_pair(key_size=2048):
    """
    Generates RSA key pair (public + private).
    Returns PEM encoded strings.
    """
    key = RSA.generate(key_size)
    private_key = key.export_key().decode()
    public_key = key.publickey().export_key().decode()
    return public_key, private_key


def encrypt_private_key(private_key_pem, password):
    """
    Encrypts a private key using AES derived from password.
    Returns base64-encoded encrypted data.
    """
    salt = get_random_bytes(16)
    key = PBKDF2(password, salt, dkLen=32, count=1000000)

    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(private_key_pem.encode())

    encrypted = {
        'salt': base64.b64encode(salt).decode(),
        'nonce': base64.b64encode(cipher.nonce).decode(),
        'tag': base64.b64encode(tag).decode(),
        'ciphertext': base64.b64encode(ciphertext).decode()
    }

    return json.dumps(encrypted)


def decrypt_private_key(encrypted_json, password):
    """
    Decrypts a private key using password.
    Only for internal use (admin/developer tools).
    """
    encrypted = json.loads(encrypted_json)

    salt = base64.b64decode(encrypted['salt'])
    nonce = base64.b64decode(encrypted['nonce'])
    tag = base64.b64decode(encrypted['tag'])
    ciphertext = base64.b64decode(encrypted['ciphertext'])

    key = PBKDF2(password, salt, dkLen=32, count=1000000)

    cipher = AES.new(key, AES.MODE_EAX, nonce)
    private_key = cipher.decrypt_and_verify(ciphertext, tag)

    return private_key.decode()
