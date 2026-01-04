# Copyright (c) 2025 OPPRO.NET Network
import sqlite3
import os
import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
import time

# Logger
logger = logging.getLogger(__name__)

DB_PATH = "data/globalchat.db"


class GlobalChatDatabase:
    """
    Database manager for Discord GlobalChat system.
    
    Manages channel configurations, message logging, blacklists, guild settings,
    and statistics for a cross-server global chat system.
    
    Attributes
    ----------
    DB_PATH : str
        Path to the SQLite database file
    
    Notes
    -----
    Automatically creates necessary tables and performs migrations on initialization.
    Uses context managers for database connections to ensure proper resource management.
    
    Examples
    --------
    >>> db = GlobalChatDatabase()
    >>> db.set_globalchat_channel(guild_id=123456, channel_id=789012)
    >>> channels = db.get_all_channels()
    """
    
    def __init__(self):
        self._ensure_db_dir()
        self.create_tables()
        self.migrate_database()

    def _ensure_db_dir(self):
        """
        Ensure that the data directory exists.
        
        Notes
        -----
        Creates parent directories if they don't exist. Does not raise an error
        if the directory already exists.
        """
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    def _get_connection(self):
        """
        Get a database connection.
        
        Returns
        -------
        sqlite3.Connection
            Database connection with Row factory enabled
        
        Notes
        -----
        The connection uses sqlite3.Row as row_factory, allowing dictionary-style
        access to columns.
        
        Examples
        --------
        >>> with self._get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM globalchat_channels")
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """
        Check if a column exists in a table.
        
        Parameters
        ----------
        table_name : str
            Name of the database table
        column_name : str
            Name of the column to check
        
        Returns
        -------
        bool
            True if column exists, False otherwise
        
        Notes
        -----
        Returns False if any database error occurs during the check.
        
        Examples
        --------
        >>> if db._column_exists('globalchat_channels', 'guild_name'):
        ...     print("Column exists")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in c.fetchall()]
                return column_name in columns
        except sqlite3.Error:
            return False

    def migrate_database(self):
        """
        Perform database migrations.
        
        Adds missing columns to existing tables to ensure schema compatibility
        with newer versions. Migrations are idempotent and safe to run multiple times.
        
        Raises
        ------
        sqlite3.Error
            If migration fails
        
        Notes
        -----
        Automatically called during initialization. Logs each migration step.
        Critical migration: Adds 'content' column to message_log table.
        
        Examples
        --------
        >>> db = GlobalChatDatabase()  # Migrations run automatically
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Migration for globalchat_channels
                if not self._column_exists('globalchat_channels', 'guild_name'):
                    logger.info("Adding column 'guild_name' to globalchat_channels")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN guild_name TEXT")

                if not self._column_exists('globalchat_channels', 'channel_name'):
                    logger.info("Adding column 'channel_name' to globalchat_channels")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN channel_name TEXT")

                if not self._column_exists('globalchat_channels', 'created_at'):
                    logger.info("Adding column 'created_at' to globalchat_channels")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                if not self._column_exists('globalchat_channels', 'last_activity'):
                    logger.info("Adding column 'last_activity' to globalchat_channels")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                if not self._column_exists('globalchat_channels', 'message_count'):
                    logger.info("Adding column 'message_count' to globalchat_channels")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN message_count INTEGER DEFAULT 0")

                if not self._column_exists('globalchat_channels', 'is_active'):
                    logger.info("Adding column 'is_active' to globalchat_channels")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN is_active BOOLEAN DEFAULT 1")

                # CRITICAL MIGRATION: message_log content column
                if not self._column_exists('message_log', 'content'):
                    logger.info("✨ Adding column 'content' to message_log")
                    c.execute("ALTER TABLE message_log ADD COLUMN content TEXT")

                conn.commit()
                logger.info("✅ Database migration completed")

        except sqlite3.Error as e:
            logger.error(f"❌ Migration error: {e}")
            raise

    def create_tables(self):
        """
        Create all required database tables.
        
        Creates the following tables if they don't exist:
        - globalchat_channels: Channel configurations
        - message_log: Message history for moderation
        - globalchat_blacklist: Banned users and guilds
        - guild_settings: Per-guild configuration
        - daily_stats: Daily statistics
        
        Raises
        ------
        sqlite3.Error
            If table creation fails
        
        Notes
        -----
        Safe to call multiple times. Uses IF NOT EXISTS to avoid errors.
        
        Examples
        --------
        >>> db = GlobalChatDatabase()  # Tables created automatically
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # GlobalChat Channels
                c.execute("""
                    CREATE TABLE IF NOT EXISTS globalchat_channels (
                        guild_id INTEGER PRIMARY KEY,
                        channel_id INTEGER NOT NULL
                    )
                """)

                # Message Log - CORRECTED with content column
                c.execute("""
                    CREATE TABLE IF NOT EXISTS message_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        guild_id INTEGER NOT NULL,
                        channel_id INTEGER NOT NULL,
                        content TEXT,
                        attachment_urls TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Blacklist System
                c.execute("""
                    CREATE TABLE IF NOT EXISTS globalchat_blacklist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_type TEXT NOT NULL CHECK (entity_type IN ('user', 'guild')),
                        entity_id INTEGER NOT NULL,
                        reason TEXT,
                        banned_by INTEGER,
                        banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        is_permanent BOOLEAN DEFAULT 0,
                        UNIQUE(entity_type, entity_id)
                    )
                """)

                # Guild Settings
                c.execute("""
                    CREATE TABLE IF NOT EXISTS guild_settings (
                        guild_id INTEGER PRIMARY KEY,
                        filter_enabled BOOLEAN DEFAULT 1,
                        nsfw_filter BOOLEAN DEFAULT 1,
                        embed_color TEXT DEFAULT '#5865F2',
                        custom_webhook_name TEXT,
                        max_message_length INTEGER DEFAULT 1900,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Statistics
                c.execute("""
                    CREATE TABLE IF NOT EXISTS daily_stats (
                        date DATE PRIMARY KEY,
                        total_messages INTEGER DEFAULT 0,
                        active_guilds INTEGER DEFAULT 0,
                        active_users INTEGER DEFAULT 0
                    )
                """)

                conn.commit()
                logger.info("✅ Base database tables created")
        except sqlite3.Error as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise

    def set_globalchat_channel(self, guild_id: int, channel_id: int, guild_name: str = None, channel_name: str = None) -> bool:
        """
        Set a GlobalChat channel for a guild.
        
        Parameters
        ----------
        guild_id : int
            Discord guild ID
        channel_id : int
            Discord channel ID
        guild_name : str, optional
            Name of the guild (default: None)
        channel_name : str, optional
            Name of the channel (default: None)
        
        Returns
        -------
        bool
            True if successful, False otherwise
        
        Notes
        -----
        Updates existing configuration if guild already has a channel set.
        Automatically updates last_activity timestamp if the column exists.
        
        Examples
        --------
        >>> db.set_globalchat_channel(guild_id=123456, channel_id=789012)
        >>> db.set_globalchat_channel(guild_id=123456, channel_id=789012,
        ...                           guild_name="My Server", channel_name="global-chat")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                has_guild_name = self._column_exists('globalchat_channels', 'guild_name')
                has_channel_name = self._column_exists('globalchat_channels', 'channel_name')
                has_last_activity = self._column_exists('globalchat_channels', 'last_activity')

                if has_guild_name and has_channel_name and has_last_activity:
                    c.execute("""
                        INSERT OR REPLACE INTO globalchat_channels 
                        (guild_id, channel_id, guild_name, channel_name, last_activity) 
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (guild_id, channel_id, guild_name, channel_name))
                else:
                    c.execute("""
                        INSERT OR REPLACE INTO globalchat_channels 
                        (guild_id, channel_id) 
                        VALUES (?, ?)
                    """, (guild_id, channel_id))

                conn.commit()
                logger.info(f"✅ GlobalChat channel set: Guild {guild_id} -> Channel {channel_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"❌ Error setting GlobalChat channel: {e}")
            return False

    def get_all_channels(self) -> List[int]:
        """
        Get all active GlobalChat channel IDs.
        
        Returns
        -------
        list of int
            List of active channel IDs
        
        Notes
        -----
        Only returns active channels if the is_active column exists.
        Returns empty list if an error occurs.
        
        Examples
        --------
        >>> channels = db.get_all_channels()
        >>> print(f"Active channels: {len(channels)}")
        >>> for channel_id in channels:
        ...     print(f"Channel: {channel_id}")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                if self._column_exists('globalchat_channels', 'is_active'):
                    c.execute("SELECT channel_id FROM globalchat_channels WHERE is_active = 1")
                else:
                    c.execute("SELECT channel_id FROM globalchat_channels")

                result = [row['channel_id'] for row in c.fetchall()]
                logger.debug(f"📊 All active channels retrieved: {len(result)} channels")
                return result
        except sqlite3.Error as e:
            logger.error(f"❌ Error retrieving all channels: {e}")
            return []

    def get_globalchat_channel(self, guild_id: int) -> Optional[int]:
        """
        Get the channel ID for a guild.
        
        Parameters
        ----------
        guild_id : int
            Discord guild ID
        
        Returns
        -------
        int or None
            Channel ID if found, None otherwise
        
        Notes
        -----
        Only returns channel if it's marked as active (when is_active column exists).
        
        Examples
        --------
        >>> channel_id = db.get_globalchat_channel(123456)
        >>> if channel_id:
        ...     print(f"Guild has channel: {channel_id}")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                if self._column_exists('globalchat_channels', 'is_active'):
                    c.execute("SELECT channel_id FROM globalchat_channels WHERE guild_id = ? AND is_active = 1", (guild_id,))
                else:
                    c.execute("SELECT channel_id FROM globalchat_channels WHERE guild_id = ?", (guild_id,))

                result = c.fetchone()
                return result['channel_id'] if result else None
        except sqlite3.Error as e:
            logger.error(f"❌ Error retrieving channel for guild {guild_id}: {e}")
            return None

    def remove_globalchat_channel(self, guild_id: int) -> bool:
        """
        Remove a GlobalChat channel configuration.
        
        Parameters
        ----------
        guild_id : int
            Discord guild ID
        
        Returns
        -------
        bool
            True if channel was removed, False if not found or error occurred
        
        Examples
        --------
        >>> if db.remove_globalchat_channel(123456):
        ...     print("Channel removed successfully")
        ... else:
        ...     print("No channel found or error occurred")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM globalchat_channels WHERE guild_id = ?", (guild_id,))
                changes = c.rowcount
                conn.commit()

                if changes > 0:
                    logger.info(f"✅ GlobalChat channel removed for guild {guild_id}")
                    return True
                else:
                    logger.warning(f"⚠️ No channel found for guild {guild_id}")
                    return False
        except sqlite3.Error as e:
            logger.error(f"❌ Error removing GlobalChat channel: {e}")
            return False

    def update_channel_activity(self, guild_id: int):
        """
        Update last activity and increment message count.
        
        Parameters
        ----------
        guild_id : int
            Discord guild ID
        
        Notes
        -----
        Only updates fields that exist in the schema. Safe to call even if
        columns don't exist yet.
        
        Examples
        --------
        >>> db.update_channel_activity(123456)
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                has_last_activity = self._column_exists('globalchat_channels', 'last_activity')
                has_message_count = self._column_exists('globalchat_channels', 'message_count')

                if has_last_activity and has_message_count:
                    c.execute("""
                        UPDATE globalchat_channels 
                        SET last_activity = CURRENT_TIMESTAMP, message_count = message_count + 1 
                        WHERE guild_id = ?
                    """, (guild_id,))
                elif has_message_count:
                    c.execute("""
                        UPDATE globalchat_channels 
                        SET message_count = message_count + 1 
                        WHERE guild_id = ?
                    """, (guild_id,))

                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"❌ Error updating activity: {e}")

    def log_message(self, user_id: int, guild_id: int, channel_id: int, content: str, attachment_urls: str = None):
        """
        Log a message for moderation purposes.
        
        Parameters
        ----------
        user_id : int
            Discord user ID who sent the message
        guild_id : int
            Discord guild ID where message was sent
        channel_id : int
            Discord channel ID where message was sent
        content : str
            Message content
        attachment_urls : str, optional
            URLs of message attachments (default: None)
        
        Notes
        -----
        Logs are used for moderation and can be retrieved with get_user_message_history().
        
        Examples
        --------
        >>> db.log_message(user_id=123456, guild_id=789012, channel_id=345678,
        ...                content="Hello world!")
        >>> db.log_message(user_id=123456, guild_id=789012, channel_id=345678,
        ...                content="Check this out", attachment_urls="https://example.com/image.png")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO message_log 
                    (user_id, guild_id, channel_id, content, attachment_urls) 
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, guild_id, channel_id, content, attachment_urls))
                conn.commit()
                logger.debug(f"📝 Message logged: User {user_id} in Guild {guild_id}")
        except sqlite3.Error as e:
            logger.error(f"❌ Error logging message: {e}")

    def get_user_message_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Get recent messages from a user.
        
        Parameters
        ----------
        user_id : int
            Discord user ID
        limit : int, optional
            Maximum number of messages to retrieve (default: 10)
        
        Returns
        -------
        list of dict
            List of message dictionaries, newest first. Each dictionary contains:
            id, user_id, guild_id, channel_id, content, attachment_urls, timestamp
        
        Examples
        --------
        >>> messages = db.get_user_message_history(123456, limit=5)
        >>> for msg in messages:
        ...     print(f"{msg['timestamp']}: {msg['content']}")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT * FROM message_log 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (user_id, limit))
                return [dict(row) for row in c.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"❌ Error retrieving message history: {e}")
            return []

    def add_to_blacklist(self, entity_type: str, entity_id: int, reason: str, banned_by: int, duration_hours: int = None):
        """
        Add a user or guild to the blacklist.
        
        Parameters
        ----------
        entity_type : {'user', 'guild'}
            Type of entity to ban
        entity_id : int
            Discord ID of the user or guild
        reason : str
            Reason for the ban
        banned_by : int
            Discord user ID of the moderator issuing the ban
        duration_hours : int, optional
            Duration in hours (default: None for permanent ban)
        
        Returns
        -------
        bool
            True if successful, False otherwise
        
        Notes
        -----
        If duration_hours is None, the ban is permanent. Otherwise, it expires
        after the specified duration.
        
        Examples
        --------
        >>> db.add_to_blacklist(entity_type='user', entity_id=123456,
        ...                     reason="Spam", banned_by=789012, duration_hours=24)
        >>> db.add_to_blacklist(entity_type='guild', entity_id=345678,
        ...                     reason="Abuse", banned_by=789012)  # Permanent
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                expires_at = None
                is_permanent = duration_hours is None

                if duration_hours:
                    expires_at = datetime.now() + timedelta(hours=duration_hours)

                c.execute("""
                    INSERT OR REPLACE INTO globalchat_blacklist 
                    (entity_type, entity_id, reason, banned_by, expires_at, is_permanent) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (entity_type, entity_id, reason, banned_by, expires_at, is_permanent))
                conn.commit()
                logger.info(f"🔨 Added to blacklist: {entity_type} {entity_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"❌ Error adding to blacklist: {e}")
            return False

    def remove_from_blacklist(self, entity_type: str, entity_id: int) -> bool:
        """
        Remove a user or guild from the blacklist.
        
        Parameters
        ----------
        entity_type : {'user', 'guild'}
            Type of entity to unban
        entity_id : int
            Discord ID of the user or guild
        
        Returns
        -------
        bool
            True if entity was removed, False if not found or error occurred
        
        Examples
        --------
        >>> if db.remove_from_blacklist('user', 123456):
        ...     print("User unbanned successfully")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM globalchat_blacklist WHERE entity_type = ? AND entity_id = ?", (entity_type, entity_id))
                changes = c.rowcount
                conn.commit()

                if changes > 0:
                    logger.info(f"✅ Removed from blacklist: {entity_type} {entity_id}")
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"❌ Error removing from blacklist: {e}")
            return False

    def is_blacklisted(self, entity_type: str, entity_id: int) -> bool:
        """
        Check if a user or guild is blacklisted.
        
        Parameters
        ----------
        entity_type : {'user', 'guild'}
            Type of entity to check
        entity_id : int
            Discord ID of the user or guild
        
        Returns
        -------
        bool
            True if blacklisted, False otherwise
        
        Notes
        -----
        Automatically removes expired temporary bans when checking.
        Permanent bans always return True.
        
        Examples
        --------
        >>> if db.is_blacklisted('user', 123456):
        ...     print("User is banned")
        ... else:
        ...     print("User is not banned")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT expires_at, is_permanent FROM globalchat_blacklist 
                    WHERE entity_type = ? AND entity_id = ?
                """, (entity_type, entity_id))
                result = c.fetchone()

                if not result:
                    return False

                if result['is_permanent']:
                    return True

                if result['expires_at']:
                    expires_at = datetime.fromisoformat(result['expires_at'])
                    if datetime.now() > expires_at:
                        self.remove_from_blacklist(entity_type, entity_id)
                        return False
                    return True

                return False
        except sqlite3.Error as e:
            logger.error(f"❌ Error checking blacklist: {e}")
            return False

    def get_blacklist(self, entity_type: str = None) -> List[Dict]:
        """
        Get the complete blacklist or filtered by type.
        
        Parameters
        ----------
        entity_type : {'user', 'guild'}, optional
            Type of entities to retrieve (default: None for all)
        
        Returns
        -------
        list of dict
            List of blacklist entries. Each dictionary contains:
            id, entity_type, entity_id, reason, banned_by, banned_at,
            expires_at, is_permanent
        
        Examples
        --------
        >>> all_bans = db.get_blacklist()
        >>> user_bans = db.get_blacklist(entity_type='user')
        >>> for ban in user_bans:
        ...     print(f"User {ban['entity_id']}: {ban['reason']}")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                if entity_type:
                    c.execute("SELECT * FROM globalchat_blacklist WHERE entity_type = ?", (entity_type,))
                else:
                    c.execute("SELECT * FROM globalchat_blacklist")
                return [dict(row) for row in c.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"❌ Error retrieving blacklist: {e}")
            return []

    def get_guild_settings(self, guild_id: int) -> Dict:
        """
        Get settings for a guild.
        
        Parameters
        ----------
        guild_id : int
            Discord guild ID
        
        Returns
        -------
        dict
            Dictionary containing guild settings. If no custom settings exist,
            returns default settings. Keys: guild_id, filter_enabled, nsfw_filter,
            embed_color, custom_webhook_name, max_message_length
        
        Examples
        --------
        >>> settings = db.get_guild_settings(123456)
        >>> print(f"Filter enabled: {settings['filter_enabled']}")
        >>> print(f"Embed color: {settings['embed_color']}")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
                result = c.fetchone()

                if result:
                    return dict(result)
                else:
                    return {
                        'guild_id': guild_id,
                        'filter_enabled': True,
                        'nsfw_filter': True,
                        'embed_color': '#5865F2',
                        'custom_webhook_name': None,
                        'max_message_length': 1900
                    }
        except sqlite3.Error as e:
            logger.error(f"❌ Error retrieving guild settings: {e}")
            return {}

    def update_guild_setting(self, guild_id: int, setting_name: str, value) -> bool:
        """
        Update a guild setting.
        
        Parameters
        ----------
        guild_id : int
            Discord guild ID
        setting_name : str
            Name of the setting to update (must match column name)
        value : Any
            New value for the setting
        
        Returns
        -------
        bool
            True if successful, False otherwise
        
        Notes
        -----
        Creates guild_settings entry if it doesn't exist.
        Valid setting names: filter_enabled, nsfw_filter, embed_color,
        custom_webhook_name, max_message_length
        
        Examples
        --------
        >>> db.update_guild_setting(123456, 'filter_enabled', False)
        >>> db.update_guild_setting(123456, 'embed_color', '#FF5733')
        >>> db.update_guild_setting(123456, 'max_message_length', 2000)
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT guild_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
                if not c.fetchone():
                    c.execute("INSERT INTO guild_settings (guild_id) VALUES (?)", (guild_id,))

                c.execute(f"UPDATE guild_settings SET {setting_name} = ? WHERE guild_id = ?", (value, guild_id))
                conn.commit()
                logger.debug(f"⚙️ Setting updated: {setting_name} = {value} for Guild {guild_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"❌ Error updating guild settings: {e}")
            return False

    def get_global_stats(self) -> Dict:
        """
        Get global statistics.
        
        Returns
        -------
        dict
            Dictionary containing global statistics. Keys: active_guilds,
            total_messages, today_messages, banned_users, banned_guilds
        
        Notes
        -----
        Returns empty dict if an error occurs.
        
        Examples
        --------
        >>> stats = db.get_global_stats()
        >>> print(f"Active guilds: {stats['active_guilds']}")
        >>> print(f"Total messages: {stats['total_messages']}")
        >>> print(f"Banned users: {stats['banned_users']}")
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                if self._column_exists('globalchat_channels', 'is_active'):
                    c.execute("SELECT COUNT(*) as count FROM globalchat_channels WHERE is_active = 1")
                else:
                    c.execute("SELECT COUNT(*) as count FROM globalchat_channels")
                active_guilds = c.fetchone()['count']

                c.execute("SELECT total_messages FROM daily_stats WHERE date = DATE('now')")
                today_messages = c.fetchone()
                today_messages = today_messages['total_messages'] if today_messages else 0

                if self._column_exists('globalchat_channels', 'message_count'):
                    c.execute("SELECT SUM(message_count) as total FROM globalchat_channels")
                    total_messages = c.fetchone()['total'] or 0
                else:
                    total_messages = 0

                c.execute("SELECT COUNT(*) as count FROM globalchat_blacklist WHERE entity_type = 'user'")
                banned_users = c.fetchone()['count']

                c.execute("SELECT COUNT(*) as count FROM globalchat_blacklist WHERE entity_type = 'guild'")
                banned_guilds = c.fetchone()['count']

                return {
                    'active_guilds': active_guilds,
                    'total_messages': total_messages,
                    'today_messages': today_messages,
                    'banned_users': banned_users,
                    'banned_guilds': banned_guilds
                }
        except sqlite3.Error as e:
            logger.error(f"❌ Error retrieving statistics: {e}")
            return {}

    def update_daily_stats(self):
        """
        Update daily statistics.
        
        Notes
        -----
        Increments the message count for today and updates active guild count.
        Creates a new daily_stats entry if one doesn't exist for today.
        
        Examples
        --------
        >>> db.update_daily_stats()  # Call after each message
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT OR REPLACE INTO daily_stats 
                    (date, total_messages, active_guilds) 
                    SELECT 
                        DATE('now'),
                        COALESCE((SELECT total_messages FROM daily_stats WHERE date = DATE('now')), 0) + 1,
                        (SELECT COUNT(*) FROM globalchat_channels WHERE 1=1)
                """)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"❌ Error updating daily stats: {e}")

    def cleanup_old_data(self, days: int = 30):
        """
        Clean up old data from the database.
        
        Parameters
        ----------
        days : int, optional
            Number of days to keep message logs (default: 30)
        
        Notes
        -----
        Performs the following cleanup:
        - Removes message logs older than specified days
        - Removes expired temporary bans
        - Removes daily statistics older than 90 days
        
        Examples
        --------
        >>> db.cleanup_old_data(days=30)  # Keep last 30 days
        >>> db.cleanup_old_data(days=7)   # Keep only last week
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                c.execute("DELETE FROM message_log WHERE timestamp < datetime('now', '-{} days')".format(days))
                deleted_messages = c.rowcount

                c.execute("DELETE FROM globalchat_blacklist WHERE expires_at < datetime('now') AND is_permanent = 0")
                deleted_bans = c.rowcount

                c.execute("DELETE FROM daily_stats WHERE date < date('now', '-90 days')")
                deleted_stats = c.rowcount

                conn.commit()
                logger.info(f"🧹 Cleanup: {deleted_messages} messages, {deleted_bans} bans, {deleted_stats} stats deleted")
        except sqlite3.Error as e:
            logger.error(f"❌ Error during cleanup: {e}")

db = GlobalChatDatabase()