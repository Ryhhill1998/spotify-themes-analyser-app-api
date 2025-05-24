from datetime import datetime

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

    def get_top_artists(
            self,
            user_id: str,
            time_range: TopItemTimeRange,
            collected_date: str,
            limit: int
    ) -> list[DBArtist]:
        cursor = self.connection.cursor(dictionary=True)

        try:
            select_statement = (
                "SELECT * " 
                f"FROM top_artist "
                "WHERE spotify_user_id = %s "
                "AND time_range = %s "
                "AND collected_date = %s "
                "ORDER BY position "
                f"LIMIT {limit};"
            )
            cursor.execute(select_statement, (user_id, time_range.value, collected_date))
            results = cursor.fetchall()
            logger.info(f"get_top_artists results: {results}")
            top_artists = [DBArtist(**entry) for entry in results]
            return top_artists
        except mysql.connector.Error as e:
            error_message = (
                f"Failed to get top artists. User ID: {user_id}, time range: {time_range.value}, "
                f"collected_date: {collected_date}"
            )
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)
        finally:
            cursor.close()
            
    def get_top_tracks(
            self,
            user_id: str,
            time_range: TopItemTimeRange,
            collected_date: str,
            limit: int
    ) -> list[DBTrack]:
        cursor = self.connection.cursor(dictionary=True)

        try:
            select_statement = (
                "SELECT * " 
                f"FROM top_track "
                "WHERE spotify_user_id = %s "
                "AND time_range = %s "
                "AND collected_date = %s "
                "ORDER BY position "
                f"LIMIT {limit};"
            )
            cursor.execute(select_statement, (user_id, time_range.value, collected_date))
            results = cursor.fetchall()
            logger.info(f"get_top_tracks results: {results}")
            top_tracks = [DBTrack(**entry) for entry in results]
            return top_tracks
        except mysql.connector.Error as e:
            error_message = (
                f"Failed to get top tracks. User ID: {user_id}, time range: {time_range.value}, "
                f"collected_date: {collected_date}"
            )
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)
        finally:
            cursor.close()

    def get_top_genres(
            self,
            user_id: str,
            time_range: TopItemTimeRange,
            collected_date: str,
            limit: int
    ) -> list[DBGenre]:
        cursor = self.connection.cursor(dictionary=True)

        try:
            select_statement = (
                "SELECT * " 
                f"FROM top_genre "
                "WHERE spotify_user_id = %s "
                "AND time_range = %s "
                "AND collected_date = %s "
                "ORDER BY count DESC "
                f"LIMIT {limit};"
            )
            cursor.execute(select_statement, (user_id, time_range.value, collected_date))
            results = cursor.fetchall()
            logger.info(f"get_top_genres results: {results}")
            top_genres = [DBGenre(**entry) for entry in results]
            return top_genres
        except mysql.connector.Error as e:
            error_message = (
                f"Failed to get top genres. User ID: {user_id}, time range: {time_range.value}, "
                f"collected_date: {collected_date}"
            )
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)
        finally:
            cursor.close()
            
    def get_top_emotions(
            self,
            user_id: str,
            time_range: TopItemTimeRange,
            collected_date: str,
            limit: int
    ) -> list[DBEmotion]:
        cursor = self.connection.cursor(dictionary=True)

        try:
            select_statement = (
                "SELECT * " 
                f"FROM top_emotion "
                "WHERE spotify_user_id = %s "
                "AND time_range = %s "
                "AND collected_date = %s "
                "ORDER BY count DESC "
                f"LIMIT {limit};"
            )
            cursor.execute(select_statement, (user_id, time_range.value, collected_date))
            results = cursor.fetchall()
            logger.info(f"get_top_emotions results: {results}")
            top_emotions = [DBEmotion(**entry) for entry in results]
            return top_emotions
        except mysql.connector.Error as e:
            error_message = (
                f"Failed to get top emotions. User ID: {user_id}, time range: {time_range.value}, "
                f"collected_date: {collected_date}"
            )
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)
        finally:
            cursor.close()
