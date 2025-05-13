import mysql.connector
from mysql.connector.pooling import PooledMySQLConnection
from loguru import logger

from api.data_structures.enums import TopItemType, TopItemTimeRange


class DBServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class DBService:
    def __init__(self, connection: PooledMySQLConnection):
        self.connection = connection

    def create_user(self, user_id: str, refresh_token: str):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO spotify_user (id, refresh_token) VALUES (%s, %s);",
                (user_id, refresh_token)
            )
            cursor.close()
            self.connection.commit()
        except mysql.connector.IntegrityError as e:
            logger.info(f"User already exists: {user_id} - {e}")
        except mysql.connector.Error as e:
            self.connection.rollback()
            error_message = f"Failed to create user. User ID: {user_id}, refresh token: {refresh_token}"
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)

    def get_top_items(
            self,
            user_id: str,
            item_type: TopItemType,
            time_range: TopItemTimeRange,
            limit: int
    ) -> list[dict]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            select_statement = (
                "WITH most_recent_date AS ("
                    "SELECT collected_date "
                    f"FROM top_{item_type.value} "
                    "WHERE spotify_user_id = %s "
                    "AND time_range = %s "
                    "ORDER BY collected_date DESC "
                    "LIMIT 1"
                ") "
                "SELECT * " 
                f"FROM top_{item_type.value} t "
                "JOIN most_recent_date rd " 
                "ON t.collected_date = rd.collected_date "
                "WHERE t.spotify_user_id = %s "
                "AND t.time_range = %s "
                "ORDER BY t.position "
                f"LIMIT {limit};"
            )
            logger.info(f"Select query: {select_statement, (user_id, time_range.value, user_id, time_range.value)}")
            cursor.execute(select_statement, (user_id, time_range.value, user_id, time_range.value))
            results = cursor.fetchall()
            logger.info(f"get_top_items results: {results}")
            cursor.close()
            return results
        except mysql.connector.Error as e:
            error_message = f"Failed to get top {item_type.value}s. User ID: {user_id}, time range: {time_range.value}"
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)
