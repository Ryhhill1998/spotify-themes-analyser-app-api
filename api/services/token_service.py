import jwt


class TokenService:
    def __init__(self, secret_key: str, encryption_algorithm: str):
        self.secret_key = secret_key
        self.encryption_algorithm = encryption_algorithm

    def create_token(self, payload: dict) -> str:
        return jwt.encode(payload=payload, key=self.secret_key, algorithm=self.encryption_algorithm)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(jwt=token, key=self.secret_key, algorithms=[self.encryption_algorithm])
