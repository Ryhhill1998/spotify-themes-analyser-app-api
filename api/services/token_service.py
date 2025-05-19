import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey


class TokenService:
    def __init__(self, private_key: RSAPrivateKey, public_key: RSAPublicKey, encryption_algorithm: str):
        self.private_key = private_key
        self.public_key = public_key
        self.encryption_algorithm = encryption_algorithm

    def create_token(self, payload: dict) -> str:
        return jwt.encode(payload=payload, key=self.private_key, algorithm=self.encryption_algorithm)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(jwt=token, key=self.public_key, algorithms=[self.encryption_algorithm])
