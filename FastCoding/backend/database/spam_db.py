import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from contextlib import contextmanager

from colorama import Fore, Style


class SpamDBError(Exception):
    """Custom exception for SpamDB errors"""
    pass


class SpamDB:
    def __init__(self, db_path='data/spam.db'):
        """Initialize spam database with enhanced error handling and logging."""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
            self.create_tables()
            self._init_database()
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise SpamDBError(f"Database initialization failed: {e}")

    @contextmanager
    def get_cursor(self):
        """Context manager for database operations with proper error handling."""
        cursor = self.conn.cursor()
        try:
            yield cursor
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise SpamDBError(f"Database operation failed: {e}")
        finally:
            cursor.close()

    def create_tables(self):
        """Create all necessary tables with improved schema."""
        with self.get_cursor() as cursor:
            # Spam settings table with better constraints
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_settings (
                    guild_id INTEGER PRIMARY KEY,
                    max_messages INTEGER DEFAULT 5 CHECK (max_messages > 0),
                    time_frame INTEGER DEFAULT 10 CHECK (time_frame > 0),
                    log_channel_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Spam logs with better indexing
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    message_count INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES spam_settings(guild_id)
                )
            ''')

            # Whitelist with better constraints
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    added_by INTEGER,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    UNIQUE(guild_id, user_id)
                )
            ''')

            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_spam_logs_guild_timestamp 
                ON spam_logs(guild_id, timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_spam_logs_user_timestamp 
                ON spam_logs(user_id, timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_whitelist_guild_user 
                ON spam_whitelist(guild_id, user_id)
            ''')

            self.conn.commit()

    def _init_database(self):
        """Initialize database with any required default data."""
        # Add any initialization logic here if needed
        pass

    def set_spam_settings(self, guild_id: int, max_messages: int = 5,
                          time_frame: int = 10, log_channel_id: Optional[int] = None) -> bool:
        """Set spam detection settings for a guild with validation."""
        if max_messages <= 0 or time_frame <= 0:
            raise SpamDBError("max_messages and time_frame must be positive integers")

        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO spam_settings 
                (guild_id, max_messages, time_frame, log_channel_id, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (guild_id, max_messages, time_frame, log_channel_id))
            self.conn.commit()
            return True

    def set_log_channel(self, guild_id: int, channel_id: int) -> bool:
        """Set the log channel for a guild."""
        with self.get_cursor() as cursor:
            # Get current settings or use defaults
            cursor.execute('SELECT max_messages, time_frame FROM spam_settings WHERE guild_id = ?',
                           (guild_id,))
            result = cursor.fetchone()

            if result:
                max_messages, time_frame = result['max_messages'], result['time_frame']
            else:
                max_messages, time_frame = 5, 10  # Default values

            cursor.execute('''
                INSERT OR REPLACE INTO spam_settings 
                (guild_id, max_messages, time_frame, log_channel_id, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (guild_id, max_messages, time_frame, channel_id))
            self.conn.commit()
            return True

    def get_spam_settings(self, guild_id: int) -> Optional[Dict]:
        """Get spam settings for a guild."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT max_messages, time_frame, log_channel_id, created_at, updated_at 
                FROM spam_settings WHERE guild_id = ?
            ''', (guild_id,))
            result = cursor.fetchone()

            if result:
                return {
                    'max_messages': result['max_messages'],
                    'time_frame': result['time_frame'],
                    'log_channel_id': result['log_channel_id'],
                    'created_at': result['created_at'],
                    'updated_at': result['updated_at']
                }
            return None

    def get_log_channel(self, guild_id: int) -> Optional[int]:
        """Get the log channel ID for a guild."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT log_channel_id FROM spam_settings WHERE guild_id = ?
            ''', (guild_id,))
            result = cursor.fetchone()
            return result['log_channel_id'] if result and result['log_channel_id'] else None

    def log_spam(self, guild_id: int, user_id: int, message: str, message_count: int = 1) -> bool:
        """Log a spam incident with message count."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO spam_logs (guild_id, user_id, message, message_count)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, user_id, message[:1000], message_count))  # Limit message length
            self.conn.commit()
            return True

    def get_spam_logs(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Get recent spam logs for a guild."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT user_id, message, message_count, timestamp 
                FROM spam_logs WHERE guild_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (guild_id, limit))

            return [
                {
                    'user_id': row['user_id'],
                    'message': row['message'],
                    'message_count': row['message_count'],
                    'timestamp': row['timestamp']
                }
                for row in cursor.fetchall()
            ]

    def get_user_spam_history(self, guild_id: int, user_id: int,
                              hours: int = 24, limit: int = 50) -> List[Dict]:
        """Get spam history for a specific user within a time frame."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT message, message_count, timestamp 
                FROM spam_logs 
                WHERE guild_id = ? AND user_id = ? AND timestamp > ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (guild_id, user_id, cutoff_time, limit))

            return [
                {
                    'message': row['message'],
                    'message_count': row['message_count'],
                    'timestamp': row['timestamp']
                }
                for row in cursor.fetchall()
            ]

    def clear_spam_logs(self, guild_id: int, older_than_days: Optional[int] = None) -> int:
        """Clear spam logs for a guild, optionally only older entries."""
        with self.get_cursor() as cursor:
            if older_than_days:
                cutoff_date = datetime.now() - timedelta(days=older_than_days)
                cursor.execute('''
                    DELETE FROM spam_logs 
                    WHERE guild_id = ? AND timestamp < ?
                ''', (guild_id, cutoff_date))
            else:
                cursor.execute('DELETE FROM spam_logs WHERE guild_id = ?', (guild_id,))

            deleted_count = cursor.rowcount
            self.conn.commit()
            return deleted_count

    def add_to_whitelist(self, guild_id: int, user_id: int,
                         added_by: Optional[int] = None, reason: Optional[str] = None) -> bool:
        """Add user to spam whitelist with additional metadata."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT OR IGNORE INTO spam_whitelist (guild_id, user_id, added_by, reason)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, user_id, added_by, reason))
            success = cursor.rowcount > 0
            self.conn.commit()
            return success

    def remove_from_whitelist(self, guild_id: int, user_id: int) -> bool:
        """Remove user from spam whitelist."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                DELETE FROM spam_whitelist WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id))
            success = cursor.rowcount > 0
            self.conn.commit()
            return success

    def is_whitelisted(self, guild_id: int, user_id: int) -> bool:
        """Check if user is whitelisted."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT 1 FROM spam_whitelist WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id))
            return cursor.fetchone() is not None

    def get_whitelist(self, guild_id: int) -> List[Dict]:
        """Get all whitelisted users for a guild with metadata."""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT user_id, added_by, added_at, reason 
                FROM spam_whitelist WHERE guild_id = ?
                ORDER BY added_at DESC
            ''', (guild_id,))

            return [
                {
                    'user_id': row['user_id'],
                    'added_by': row['added_by'],
                    'added_at': row['added_at'],
                    'reason': row['reason']
                }
                for row in cursor.fetchall()
            ]

    def get_guild_stats(self, guild_id: int) -> Dict:
        """Get comprehensive statistics for a guild."""
        with self.get_cursor() as cursor:
            # Get spam logs count
            cursor.execute('SELECT COUNT(*) as total FROM spam_logs WHERE guild_id = ?', (guild_id,))
            total_logs = cursor.fetchone()['total']

            # Get recent spam (last 24 hours)
            yesterday = datetime.now() - timedelta(hours=24)
            cursor.execute('''
                SELECT COUNT(*) as recent FROM spam_logs 
                WHERE guild_id = ? AND timestamp > ?
            ''', (guild_id, yesterday))
            recent_logs = cursor.fetchone()['recent']

            # Get whitelist count
            cursor.execute('SELECT COUNT(*) as count FROM spam_whitelist WHERE guild_id = ?', (guild_id,))
            whitelist_count = cursor.fetchone()['count']

            # Get top spammers (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute('''
                SELECT user_id, COUNT(*) as spam_count, SUM(message_count) as total_messages
                FROM spam_logs 
                WHERE guild_id = ? AND timestamp > ?
                GROUP BY user_id
                ORDER BY spam_count DESC
                LIMIT 5
            ''', (guild_id, week_ago))
            top_spammers = cursor.fetchall()

            return {
                'total_spam_logs': total_logs,
                'recent_spam_logs': recent_logs,
                'whitelist_count': whitelist_count,
                'top_spammers': [
                    {
                        'user_id': row['user_id'],
                        'spam_incidents': row['spam_count'],
                        'total_messages': row['total_messages']
                    }
                    for row in top_spammers
                ]
            }

    def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """Clean up old spam logs across all guilds."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        with self.get_cursor() as cursor:
            cursor.execute('DELETE FROM spam_logs WHERE timestamp < ?', (cutoff_date,))
            deleted_count = cursor.rowcount
            self.conn.commit()

            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old spam logs")

            return deleted_count

    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            backup_conn = sqlite3.connect(backup_path)
            self.conn.backup(backup_conn)
            backup_conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with proper cleanup."""
        self.close()

    def close(self):
        """Close database connection."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()