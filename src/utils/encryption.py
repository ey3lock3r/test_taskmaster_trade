from cryptography.fernet import Fernet
import os

class EncryptionUtil:
    def __init__(self, key: str = None):
        if key:
            self.key = key.encode('utf-8')
        else:
            self.key = os.getenv("ENCRYPTION_KEY")
            if self.key:
                self.key = self.key.encode('utf-8')
            else:
                raise ValueError("Encryption key not provided and ENCRYPTION_KEY environment variable not set.")
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode('utf-8')).decode('utf-8')

    def decrypt(self, encrypted_data: str) -> str:
        return self.fernet.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')

def generate_key():
    return Fernet.generate_key().decode('utf-8')

if __name__ == "__main__":
    # Example Usage:
    # Generate a key (do this once and store it securely, e.g., in an environment variable)
    key = generate_key()
    print(f"Generated Fernet Key: {key}")

    # Initialize the EncryptionUtil with the key
    # In a real application, you would load the key from a secure environment variable
    encryption_util = EncryptionUtil(key=key)

    # Data to encrypt
    api_key = "my_secret_api_key_12345"
    print(f"Original API Key: {api_key}")

    # Encrypt the data
    encrypted_api_key = encryption_util.encrypt(api_key)
    print(f"Encrypted API Key: {encrypted_api_key}")

    # Decrypt the data
    decrypted_api_key = encryption_util.decrypt(encrypted_api_key)
    print(f"Decrypted API Key: {decrypted_api_key}")

    assert api_key == decrypted_api_key
    print("Encryption and decryption successful!")