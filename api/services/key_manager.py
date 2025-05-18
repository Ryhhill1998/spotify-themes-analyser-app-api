from cryptography.hazmat.primitives import serialization

from api.data_structures.models import EncryptionKeys


class KeyManager:
    def __init__(self, keys_dir_path: str):
        self.keys_dir_path = keys_dir_path

    def load_encryption_keys(self, key_id: str) -> EncryptionKeys:
        with open(f"{self.keys_dir_path}/key_{key_id}", "rb") as key_file:
            key_bytes = key_file.read()

        with open(f"{self.keys_dir_path}/password_{key_id}", "rb") as password_file:
            key_password = password_file.read()

        private_key = serialization.load_pem_private_key(key_bytes, password=key_password)
        public_key = private_key.public_key()

        encryption_keys = EncryptionKeys(private_key=private_key, public_key=public_key)
        return encryption_keys
