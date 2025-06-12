from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jwt
from loguru import logger


class TokenServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class TokenService:
    def __init__(self, secret_key: str, encryption_algorithm: str):
        self.secret_key = secret_key
        self.encryption_algorithm = encryption_algorithm

    def create_token(self, user_id: dict) -> str:
        uk_tz = ZoneInfo("Europe/London")
        token_expiry = datetime.now(tz=uk_tz) + timedelta(days=1)

        return jwt.encode(
            payload={"user_id": user_id, "exp": token_expiry},
            key=self.secret_key,
            algorithm=self.encryption_algorithm
        )

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(jwt=token, key=self.secret_key, algorithms=[self.encryption_algorithm])
        except jwt.ExpiredSignatureError:
            error_message = "Token expired"
            logger.error(error_message)
            raise TokenServiceException(error_message)
