import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from api.services.key_manager import KeyManager


class TokenService:
    def __init__(self, private_key: RSAPrivateKey, public_key: RSAPublicKey, encryption_algorithm: str):
        self.private_key = private_key
        self.public_key = public_key
        self.encryption_algorithm = encryption_algorithm

    def create_token(self, payload: dict) -> str:
        return jwt.encode(payload=payload, key=self.private_key, algorithm=self.encryption_algorithm)

    def decode_token(self, token: str):
        return jwt.decode(jwt=token, key=self.public_key, algorithms=[self.encryption_algorithm])


km = KeyManager(keys_dir_path="../keys")
keys = km.load_encryption_keys("2de07979-9888-4bb5-974e-5ba8b3c396cf")

ts = TokenService(private_key=keys.private_key, public_key=keys.public_key, encryption_algorithm="RS256")
token = ts.create_token({"test": "test"})
print(f"{token = }")
decoded = ts.decode_token(token)
print(f"{decoded = }")
