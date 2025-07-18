import sqlite3
import asyncio
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional
import logging
from dateutil import parser  # Für robustes Datumsparsing

logger = logging.getLogger(__name__)


class StatsDB:
    """
    Handles all database operations for the Discord stats bot.
    Provides thread-safe database access for voice sessions and message tracking.
    """

    def __init__(self, db_path: str = "data/discord_stats.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._thread_lock = threading.Lock()
        self.init_database()

    def init_database(self):
        """
        Initialize the database with required tables.
        Creates voice_sessions and messages tables if they don't exist.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Voice sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS voice_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        channel_id INTEGER NOT NULL,
                        join_time TEXT NOT NULL,
                        leave_time TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Messages table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        channel_id INTEGER NOT NULL,
                        message_id INTEGER NOT NULL UNIQUE,
                        timestamp TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.info("Database initialized successfully")

        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    async def start_voice_session(self, user_id: int, channel_id: int) -> None:
        """
        Start a new voice session for a user.

        Args:
            user_id: Discord user ID
            channel_id: Discord voice channel ID
        """
        async with self._lock:
            try:
                join_time = datetime.now(timezone.utc).isoformat()

                def _insert():
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO voice_sessions (user_id, channel_id, join_time)
                            VALUES (?, ?, ?)
                        ''', (user_id, channel_id, join_time))
                        conn.commit()

                await asyncio.get_event_loop().run_in_executor(None, _insert)
                logger.debug(f"Started voice session for user {user_id} in channel {channel_id}")

            except sqlite3.Error as e:
                logger.error(f"Error starting voice session: {e}")
                raise

    async def end_voice_session(self, user_id: int, channel_id: int) -> None:
        """
        End the most recent active voice session for a user in a specific channel.

        Args:
            user_id: Discord user ID
            channel_id: Discord voice channel ID
        """
        async with self._lock:
            try:
                leave_time = datetime.now(timezone.utc).isoformat()

                def _update():
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()

                        # First, find the most recent active session
                        cursor.execute('''
                            SELECT id FROM voice_sessions
                            WHERE user_id = ? AND channel_id = ? AND leave_time IS NULL
                            ORDER BY join_time DESC
                            LIMIT 1
                        ''', (user_id, channel_id))

                        result = cursor.fetchone()
                        if result:
                            session_id = result[0]
                            # Update the specific session
                            cursor.execute('''
                                UPDATE voice_sessions 
                                SET leave_time = ?
                                WHERE id = ?
                            ''', (leave_time, session_id))
                            conn.commit()
                            return cursor.rowcount
                        else:
                            return 0

                rows_affected = await asyncio.get_event_loop().run_in_executor(None, _update)

                if rows_affected > 0:
                    logger.debug(f"Ended voice session for user {user_id} in channel {channel_id}")
                else:
                    logger.warning(f"No active voice session found for user {user_id} in channel {channel_id}")

            except sqlite3.Error as e:
                logger.error(f"Error ending voice session: {e}")
                raise

    async def end_all_user_sessions(self, user_id: int) -> None:
        """
        End all active voice sessions for a user (used when user disconnects completely).

        Args:
            user_id: Discord user ID
        """
        async with self._lock:
            try:
                leave_time = datetime.now(timezone.utc).isoformat()

                def _update():
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE voice_sessions 
                            SET leave_time = ?
                            WHERE user_id = ? AND leave_time IS NULL
                        ''', (leave_time, user_id))
                        conn.commit()
                        return cursor.rowcount

                rows_affected = await asyncio.get_event_loop().run_in_executor(None, _update)
                logger.debug(f"Ended {rows_affected} active sessions for user {user_id}")

            except sqlite3.Error as e:
                logger.error(f"Error ending all user sessions: {e}")
                raise

    async def log_message(self, user_id: int, channel_id: int, message_id: int) -> None:
        """
        Log a message to the database.

        Args:
            user_id: Discord user ID
            channel_id: Discord channel ID
            message_id: Discord message ID
        """
        async with self._lock:
            try:
                timestamp = datetime.now(timezone.utc).isoformat()

                def _insert():
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR IGNORE INTO messages (user_id, channel_id, message_id, timestamp)
                            VALUES (?, ?, ?, ?)
                        ''', (user_id, channel_id, message_id, timestamp))
                        conn.commit()

                await asyncio.get_event_loop().run_in_executor(None, _insert)
                logger.debug(f"Logged message {message_id} from user {user_id}")

            except sqlite3.Error as e:
                logger.error(f"Error logging message: {e}")
                raise

    async def get_user_stats(self, user_id: int, hours: int) -> Tuple[int, float]:
        """
        Get user statistics for a given time period.

        Args:
            user_id: Discord user ID
            hours: Number of hours to look back

        Returns:
            Tuple of (message_count, voice_time_minutes)
        """
        async with self._lock:
            try:
                def _get_stats():
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        now = datetime.now(timezone.utc)
                        cutoff_start = now - timedelta(hours=hours)
                        cutoff_start_iso = cutoff_start.isoformat()
                        now_iso = now.isoformat()

                        # Get message count
                        cursor.execute('''
                            SELECT COUNT(*) FROM messages 
                            WHERE user_id = ? AND timestamp >= ?
                        ''', (user_id, cutoff_start_iso))
                        message_count = cursor.fetchone()[0]

                        # Get voice sessions that overlap with the timeframe
                        cursor.execute('''
                            SELECT join_time, leave_time FROM voice_sessions
                            WHERE user_id = ?
                              AND (leave_time IS NULL OR leave_time >= ?)
                              AND join_time <= ?
                        ''', (user_id, cutoff_start_iso, now_iso))

                        voice_sessions = cursor.fetchall()
                        total_voice_seconds = 0

                        for join_str, leave_str in voice_sessions:
                            try:
                                join_time = parser.parse(join_str)
                            except Exception:
                                join_time = datetime.fromisoformat(join_str)

                            if leave_str:
                                try:
                                    leave_time = parser.parse(leave_str)
                                except Exception:
                                    leave_time = datetime.fromisoformat(leave_str)
                            else:
                                leave_time = now

                            session_start = max(join_time, cutoff_start)
                            session_end = min(leave_time, now)

                            if session_end > session_start:
                                total_voice_seconds += (session_end - session_start).total_seconds()

                        total_voice_minutes = total_voice_seconds / 60
                        return message_count, total_voice_minutes

                return await asyncio.get_event_loop().run_in_executor(None, _get_stats)

            except sqlite3.Error as e:
                logger.error(f"Error getting user stats: {e}")
                raise

    async def cleanup_old_data(self, days: int = 90) -> None:
        """
        Clean up old data from the database (optional maintenance function).

        Args:
            days: Number of days to keep data for
        """
        async with self._lock:
            try:
                def _cleanup():
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cutoff_time = datetime.now(timezone.utc).timestamp() - (days * 24 * 3600)
                        cutoff_iso = datetime.fromtimestamp(cutoff_time, timezone.utc).isoformat()

                        # Clean up old voice sessions
                        cursor.execute('''
                            DELETE FROM voice_sessions 
                            WHERE join_time < ? AND (leave_time IS NOT NULL AND leave_time < ?)
                        ''', (cutoff_iso, cutoff_iso))

                        # Clean up old messages
                        cursor.execute('''
                            DELETE FROM messages WHERE timestamp < ?
                        ''', (cutoff_iso,))

                        conn.commit()
                        logger.info(f"Cleaned up data older than {days} days")

                await asyncio.get_event_loop().run_in_executor(None, _cleanup)

            except sqlite3.Error as e:
                logger.error(f"Error during cleanup: {e}")
                raise
