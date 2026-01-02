# Copyright (c) 2025 OPPRO.NET Network
# File: logging_database.py

import sqlite3
import asyncio
import os
from typing import Optional, Dict, List
import threading
import logging

# Setup logging
logger = logging.getLogger(__name__)

class LoggingDatabase:
    """
    Improved database class for Discord logging system
    Handles all database operations for log channel configurations
    """
    
    def __init__(self, db_path: str = "data/log_channels.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._ensure_directory()
        self.init_db()

    def _ensure_directory(self):
        """Stellt sicher, dass das data/ Verzeichnis existiert"""
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def init_db(self):
        """Erstellt die Tabelle für Log-Channels mit verbesserter Struktur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Neue Tabelle mit separaten Einträgen für verschiedene Log-Typen
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS log_channels (
                        guild_id INTEGER NOT NULL,
                        log_type TEXT NOT NULL,
                        channel_id INTEGER NOT NULL,
                        enabled BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (guild_id, log_type)
                    )
                ''')
                
                # Index für bessere Performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_guild_enabled 
                    ON log_channels (guild_id, enabled)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_channel_id 
                    ON log_channels (channel_id)
                ''')
                
                # Migration von alter Struktur falls nötig
                cursor.execute("PRAGMA table_info(log_channels)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'log_type' not in columns:
                    logger.info("Migrating old database structure...")
                    # Backup der alten Daten
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS log_channels_backup AS 
                        SELECT * FROM log_channels
                    ''')
                    
                    # Neue Struktur erstellen
                    cursor.execute('DROP TABLE log_channels')
                    cursor.execute('''
                        CREATE TABLE log_channels (
                            guild_id INTEGER NOT NULL,
                            log_type TEXT NOT NULL DEFAULT 'general',
                            channel_id INTEGER NOT NULL,
                            enabled BOOLEAN DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (guild_id, log_type)
                        )
                    ''')
                    
                    # Alte Daten migrieren
                    cursor.execute('''
                        INSERT INTO log_channels (guild_id, log_type, channel_id, enabled)
                        SELECT guild_id, 'general', channel_id, enabled 
                        FROM log_channels_backup
                    ''')
                    
                    cursor.execute('DROP TABLE log_channels_backup')
                    logger.info("Database migration completed successfully")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    async def set_log_channel(self, guild_id: int, channel_id: int, log_type: str = 'general'):
        """Setzt den Log-Channel für einen bestimmten Log-Typ"""
        def _insert():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO log_channels 
                            (guild_id, log_type, channel_id, enabled, updated_at)
                            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (guild_id, log_type, channel_id, True))
                        conn.commit()
                        logger.debug(f"Set log channel: Guild {guild_id}, Type {log_type}, Channel {channel_id}")
            except Exception as e:
                logger.error(f"Error setting log channel: {e}")
                raise

        await asyncio.get_event_loop().run_in_executor(None, _insert)

    async def get_log_channel(self, guild_id: int, log_type: str = 'general') -> Optional[int]:
        """Holt die Channel-ID für einen Server und Log-Typ"""
        def _select():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT channel_id FROM log_channels 
                            WHERE guild_id = ? AND log_type = ? AND enabled = 1
                        ''', (guild_id, log_type))
                        row = cursor.fetchone()
                        result = row[0] if row else None
                        logger.debug(f"Get log channel: Guild {guild_id}, Type {log_type} -> {result}")
                        return result
            except Exception as e:
                logger.error(f"Error getting log channel: {e}")
                return None

        return await asyncio.get_event_loop().run_in_executor(None, _select)

    async def get_all_log_channels(self, guild_id: int) -> Dict[str, int]:
        """Holt alle konfigurierten Log-Channels für einen Server"""
        def _select_all():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT log_type, channel_id FROM log_channels 
                            WHERE guild_id = ? AND enabled = 1
                            ORDER BY log_type
                        ''', (guild_id,))
                        result = dict(cursor.fetchall())
                        logger.debug(f"Get all log channels for guild {guild_id}: {len(result)} types")
                        return result
            except Exception as e:
                logger.error(f"Error getting all log channels: {e}")
                return {}

        return await asyncio.get_event_loop().run_in_executor(None, _select_all)

    async def remove_log_channel(self, guild_id: int, log_type: str = None):
        """Entfernt Log-Channel(s) für einen Server"""
        def _delete():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        if log_type:
                            cursor.execute('''
                                DELETE FROM log_channels 
                                WHERE guild_id = ? AND log_type = ?
                            ''', (guild_id, log_type))
                            logger.debug(f"Removed log channel: Guild {guild_id}, Type {log_type}")
                        else:
                            cursor.execute('''
                                DELETE FROM log_channels WHERE guild_id = ?
                            ''', (guild_id,))
                            logger.debug(f"Removed all log channels for guild {guild_id}")
                        
                        deleted_count = cursor.rowcount
                        conn.commit()
                        return deleted_count
            except Exception as e:
                logger.error(f"Error removing log channel: {e}")
                return 0

        return await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def remove_all_log_channels(self, guild_id: int):
        """Entfernt alle Log-Channels für einen Server"""
        return await self.remove_log_channel(guild_id)

    async def disable_logging(self, guild_id: int, log_type: str = None):
        """Deaktiviert das Logging für einen Server (alle Typen oder spezifischen Typ)"""
        def _update():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        if log_type:
                            cursor.execute('''
                                UPDATE log_channels SET enabled = 0 
                                WHERE guild_id = ? AND log_type = ?
                            ''', (guild_id, log_type))
                        else:
                            cursor.execute('''
                                UPDATE log_channels SET enabled = 0 WHERE guild_id = ?
                            ''', (guild_id,))
                        updated_count = cursor.rowcount
                        conn.commit()
                        logger.debug(f"Disabled logging: Guild {guild_id}, Type {log_type}, Count {updated_count}")
                        return updated_count
            except Exception as e:
                logger.error(f"Error disabling logging: {e}")
                return 0

        return await asyncio.get_event_loop().run_in_executor(None, _update)

    async def enable_logging(self, guild_id: int, log_type: str = None):
        """Aktiviert das Logging für einen Server (alle Typen oder spezifischen Typ)"""
        def _update():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        if log_type:
                            cursor.execute('''
                                UPDATE log_channels SET enabled = 1 
                                WHERE guild_id = ? AND log_type = ?
                            ''', (guild_id, log_type))
                        else:
                            cursor.execute('''
                                UPDATE log_channels SET enabled = 1 WHERE guild_id = ?
                            ''', (guild_id,))
                        updated_count = cursor.rowcount
                        conn.commit()
                        logger.debug(f"Enabled logging: Guild {guild_id}, Type {log_type}, Count {updated_count}")
                        return updated_count
            except Exception as e:
                logger.error(f"Error enabling logging: {e}")
                return 0

        return await asyncio.get_event_loop().run_in_executor(None, _update)

    async def channel_exists(self, guild_id: int, log_type: str) -> bool:
        """Prüft ob ein Log-Channel für den Typ existiert"""
        def _exists():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT 1 FROM log_channels 
                            WHERE guild_id = ? AND log_type = ?
                        ''', (guild_id, log_type))
                        return cursor.fetchone() is not None
            except Exception as e:
                logger.error(f"Error checking channel existence: {e}")
                return False

        return await asyncio.get_event_loop().run_in_executor(None, _exists)

    async def get_guilds_with_logging(self) -> List[int]:
        """Holt alle Guild-IDs die Logging aktiviert haben"""
        def _select_guilds():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT DISTINCT guild_id FROM log_channels WHERE enabled = 1
                        ''')
                        result = [row[0] for row in cursor.fetchall()]
                        logger.debug(f"Found {len(result)} guilds with logging enabled")
                        return result
            except Exception as e:
                logger.error(f"Error getting guilds with logging: {e}")
                return []

        return await asyncio.get_event_loop().run_in_executor(None, _select_guilds)

    async def get_channels_by_guild(self, guild_id: int) -> List[Dict]:
        """Holt detaillierte Channel-Info für eine Guild"""
        def _select_detailed():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT log_type, channel_id, enabled, created_at, updated_at 
                            FROM log_channels 
                            WHERE guild_id = ?
                            ORDER BY log_type
                        ''', (guild_id,))
                        
                        columns = ['log_type', 'channel_id', 'enabled', 'created_at', 'updated_at']
                        return [dict(zip(columns, row)) for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error getting detailed channels: {e}")
                return []

        return await asyncio.get_event_loop().run_in_executor(None, _select_detailed)

    async def cleanup_invalid_channels(self, valid_channel_ids: set):
        """Entfernt ungültige Channel-IDs aus der Datenbank"""
        def _cleanup():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        if valid_channel_ids:
                            placeholders = ','.join('?' * len(valid_channel_ids))
                            cursor.execute(f'''
                                DELETE FROM log_channels 
                                WHERE channel_id NOT IN ({placeholders})
                            ''', list(valid_channel_ids))
                        else:
                            # Wenn keine gültigen Channels vorhanden, alle löschen
                            cursor.execute('DELETE FROM log_channels')
                        
                        deleted = cursor.rowcount
                        conn.commit()
                        
                        if deleted > 0:
                            logger.info(f"Cleaned up {deleted} invalid channel entries")
                        
                        return deleted
            except Exception as e:
                logger.error(f"Error cleaning up channels: {e}")
                return 0

        return await asyncio.get_event_loop().run_in_executor(None, _cleanup)

    async def get_statistics(self) -> Dict:
        """Holt Datenbankstatistiken"""
        def _get_stats():
            try:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        stats = {}
                        
                        # Total entries
                        cursor.execute('SELECT COUNT(*) FROM log_channels')
                        stats['total_entries'] = cursor.fetchone()[0]
                        
                        # Enabled entries
                        cursor.execute('SELECT COUNT(*) FROM log_channels WHERE enabled = 1')
                        stats['enabled_entries'] = cursor.fetchone()[0]
                        
                        # Unique guilds
                        cursor.execute('SELECT COUNT(DISTINCT guild_id) FROM log_channels')
                        stats['unique_guilds'] = cursor.fetchone()[0]
                        
                        # Unique channels
                        cursor.execute('SELECT COUNT(DISTINCT channel_id) FROM log_channels')
                        stats['unique_channels'] = cursor.fetchone()[0]
                        
                        # Log types distribution
                        cursor.execute('''
                            SELECT log_type, COUNT(*) FROM log_channels 
                            WHERE enabled = 1 
                            GROUP BY log_type
                        ''')
                        stats['log_types'] = dict(cursor.fetchall())
                        
                        return stats
            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                return {}

        return await asyncio.get_event_loop().run_in_executor(None, _get_stats)

    async def backup_database(self, backup_path: str = None) -> bool:
        """Erstellt ein Backup der Datenbank"""
        if not backup_path:
            backup_path = f"{self.db_path}.backup"
        
        def _backup():
            try:
                with self._lock:
                    # Quelle öffnen
                    with sqlite3.connect(self.db_path) as source:
                        # Ziel erstellen
                        with sqlite3.connect(backup_path) as target:
                            source.backup(target)
                    
                    logger.info(f"Database backup created: {backup_path}")
                    return True
            except Exception as e:
                logger.error(f"Error creating backup: {e}")
                return False

        return await asyncio.get_event_loop().run_in_executor(None, _backup)

    def close(self):
        """Cleanup-Methode für ordnungsgemäße Schließung"""
        logger.debug("Database connection closed")
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()