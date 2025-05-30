import mysql.connector
from mysql.connector.pooling import PooledMySQLConnection
from loguru import logger

from api.data_structures.enums import TopItemType, TopItemTimeRange
from api.data_structures.models import DBUser, DBArtist, DBTrack, DBGenre, DBEmotion


class DBServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class DBService:
    def __init__(self, connection: PooledMySQLConnection):
        self.connection = connection

    def create_user(self, user_id: str, refresh_token: str):
        cursor = self.connection.cursor()

        try:
            cursor.execute(
                "INSERT INTO spotify_user (id, refresh_token) VALUES (%s, %s);",
                (user_id, refresh_token)
            )
            self.connection.commit()
        except mysql.connector.IntegrityError as e:
            logger.info(f"User already exists: {user_id} - {e}")
        except mysql.connector.Error as e:
            self.connection.rollback()
            error_message = f"Failed to create user. User ID: {user_id}, refresh token: {refresh_token}"
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)
        finally:
            cursor.close()

    def get_user(self, user_id: str) -> DBUser:
        cursor = self.connection.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM spotify_user WHERE id = %s;", (user_id, ))
            result = cursor.fetchone()

            if not result:
                raise DBServiceException(f"User not found with ID: {user_id}")

            user = DBUser(**result)
            return user
        except mysql.connector.Error as e:
            error_message = f"Failed to get user with ID: {user_id}"
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)
        finally:
            cursor.close()

    @staticmethod
    def _create_db_items_from_data(data: list[dict], item_type: TopItemType):
        if item_type == TopItemType.ARTIST:
            return [DBArtist(**entry) for entry in data]
        elif item_type == TopItemType.TRACK:
            return [DBTrack(**entry) for entry in data]
        elif item_type == TopItemType.GENRE:
            return [DBGenre(**entry) for entry in data]
        elif item_type == TopItemType.EMOTION:
            return [DBEmotion(**entry) for entry in data]
        else:
            raise ValueError("Invalid item type")
            
    def get_top_items(
            self,
            user_id: str,
            time_range: TopItemTimeRange,
            collected_date: str,
            limit: int,
            item_type: TopItemType,
            order_field: str
    ):
        cursor = self.connection.cursor(dictionary=True)

        try:
            select_statement = (
                "SELECT * "
                f"FROM top_{item_type.value} "
                "WHERE spotify_user_id = %s "
                "AND time_range = %s "
                "AND collected_date = %s "
                f"ORDER BY {order_field} "
                f"LIMIT {limit};"
            )
            cursor.execute(select_statement, (user_id, time_range.value, collected_date))
            results = cursor.fetchall()
            logger.info(f"get top {item_type.value}s results: {results}")
            top_items = self._create_db_items_from_data(data=results, item_type=item_type)
            return top_items
        except mysql.connector.Error as e:
            error_message = (
                f"Failed to get top {item_type.value}s. User ID: {user_id}, time range: {time_range.value}, "
                f"collected_date: {collected_date}"
            )
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)
        finally:
            cursor.close()
