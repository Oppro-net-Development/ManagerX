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
    def __init__(self):
        self._ensure_db_dir()
        self.create_tables()
        self.migrate_database()

    def _ensure_db_dir(self):
        """Stellt sicher dass das data-Verzeichnis existiert"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    def _get_connection(self):
        """Gibt eine Datenbankverbindung zurück"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Für besseren Zugriff auf Spalten
        return conn

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """Prüft ob eine Spalte in einer Tabelle existiert"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in c.fetchall()]
                return column_name in columns
        except sqlite3.Error:
            return False

    def migrate_database(self):
        """Führt Datenbank-Migrationen durch"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Migration für globalchat_channels
                if not self._column_exists('globalchat_channels', 'guild_name'):
                    logger.info("Füge Spalte 'guild_name' zu globalchat_channels hinzu")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN guild_name TEXT")

                if not self._column_exists('globalchat_channels', 'channel_name'):
                    logger.info("Füge Spalte 'channel_name' zu globalchat_channels hinzu")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN channel_name TEXT")

                if not self._column_exists('globalchat_channels', 'created_at'):
                    logger.info("Füge Spalte 'created_at' zu globalchat_channels hinzu")
                    c.execute(
                        "ALTER TABLE globalchat_channels ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                if not self._column_exists('globalchat_channels', 'last_activity'):
                    logger.info("Füge Spalte 'last_activity' zu globalchat_channels hinzu")
                    c.execute(
                        "ALTER TABLE globalchat_channels ADD COLUMN last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                if not self._column_exists('globalchat_channels', 'message_count'):
                    logger.info("Füge Spalte 'message_count' zu globalchat_channels hinzu")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN message_count INTEGER DEFAULT 0")

                if not self._column_exists('globalchat_channels', 'is_active'):
                    logger.info("Füge Spalte 'is_active' zu globalchat_channels hinzu")
                    c.execute("ALTER TABLE globalchat_channels ADD COLUMN is_active BOOLEAN DEFAULT 1")

                conn.commit()
                logger.info("Datenbank-Migration abgeschlossen")

        except sqlite3.Error as e:
            logger.error(f"Fehler bei der Migration: {e}")
            raise

    def create_tables(self):
        """Erstellt alle benötigten Tabellen"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # GlobalChat Channels - Basis-Tabelle
                c.execute("""
                    CREATE TABLE IF NOT EXISTS globalchat_channels (
                        guild_id INTEGER PRIMARY KEY,
                        channel_id INTEGER NOT NULL
                    )
                """)

                # Message Log für Moderation
                c.execute("""
                    CREATE TABLE IF NOT EXISTS message_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        guild_id INTEGER NOT NULL,
                        channel_id INTEGER NOT NULL,
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

                # Statistiken
                c.execute("""
                    CREATE TABLE IF NOT EXISTS daily_stats (
                        date DATE PRIMARY KEY,
                        total_messages INTEGER DEFAULT 0,
                        active_guilds INTEGER DEFAULT 0,
                        active_users INTEGER DEFAULT 0
                    )
                """)

                conn.commit()
                logger.info("Basis-Datenbanktabellen erstellt")
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Erstellen der Tabellen: {e}")
            raise

    # Channel Management
    def set_globalchat_channel(self, guild_id: int, channel_id: int, guild_name: str = None,
                               channel_name: str = None) -> bool:
        """Setzt einen GlobalChat-Channel für eine Guild"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Prüfen welche Spalten existieren
                has_guild_name = self._column_exists('globalchat_channels', 'guild_name')
                has_channel_name = self._column_exists('globalchat_channels', 'channel_name')
                has_last_activity = self._column_exists('globalchat_channels', 'last_activity')

                if has_guild_name and has_channel_name and has_last_activity:
                    # Vollständige Version
                    c.execute("""
                        INSERT OR REPLACE INTO globalchat_channels 
                        (guild_id, channel_id, guild_name, channel_name, last_activity) 
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (guild_id, channel_id, guild_name, channel_name))
                else:
                    # Basis-Version
                    c.execute("""
                        INSERT OR REPLACE INTO globalchat_channels 
                        (guild_id, channel_id) 
                        VALUES (?, ?)
                    """, (guild_id, channel_id))

                conn.commit()
                logger.info(f"GlobalChat-Channel gesetzt: Guild {guild_id} -> Channel {channel_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Setzen des GlobalChat-Channels: {e}")
            return False

    def get_all_channels(self) -> List[int]:
        """Gibt alle aktiven GlobalChat-Channel-IDs zurück"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Prüfen ob is_active Spalte existiert
                if self._column_exists('globalchat_channels', 'is_active'):
                    c.execute("SELECT channel_id FROM globalchat_channels WHERE is_active = 1")
                else:
                    c.execute("SELECT channel_id FROM globalchat_channels")

                result = [row['channel_id'] for row in c.fetchall()]
                logger.debug(f"Alle aktiven Channels abgerufen: {len(result)} Channels")
                return result
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Abrufen aller Channels: {e}")
            return []

    def get_globalchat_channel(self, guild_id: int) -> Optional[int]:
        """Gibt die Channel-ID für eine Guild zurück"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Prüfen ob is_active Spalte existiert
                if self._column_exists('globalchat_channels', 'is_active'):
                    c.execute("""
                        SELECT channel_id FROM globalchat_channels 
                        WHERE guild_id = ? AND is_active = 1
                    """, (guild_id,))
                else:
                    c.execute("""
                        SELECT channel_id FROM globalchat_channels 
                        WHERE guild_id = ?
                    """, (guild_id,))

                result = c.fetchone()
                return result['channel_id'] if result else None
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Abrufen des Channels für Guild {guild_id}: {e}")
            return None

    def remove_globalchat_channel(self, guild_id: int) -> bool:
        """Entfernt einen GlobalChat-Channel"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM globalchat_channels WHERE guild_id = ?", (guild_id,))
                changes = c.rowcount
                conn.commit()

                if changes > 0:
                    logger.info(f"GlobalChat-Channel entfernt für Guild {guild_id}")
                    return True
                else:
                    logger.warning(f"Kein Channel für Guild {guild_id} gefunden")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Entfernen des GlobalChat-Channels: {e}")
            return False

    def update_channel_activity(self, guild_id: int):
        """Aktualisiert die letzte Aktivität und erhöht Message-Count"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Prüfen welche Spalten existieren
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
                # Wenn keine der Spalten existiert, nichts tun

                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Aktualisieren der Aktivität: {e}")

    # Message Logging
    def log_message(self, user_id: int, guild_id: int, channel_id: int, content: str,
                    attachment_urls: List[str] = None):
        """Loggt eine Nachricht für Moderation"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                attachment_str = ",".join(attachment_urls) if attachment_urls else None
                c.execute("""
                    INSERT INTO message_log 
                    (user_id, guild_id, channel_id, attachment_urls) 
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, guild_id, channel_id, content, attachment_str))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Loggen der Nachricht: {e}")

    def get_user_message_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Holt die letzten Nachrichten eines Users"""
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
            logger.error(f"Fehler beim Abrufen der Nachrichtenhistorie: {e}")
            return []

    # Blacklist System
    def add_to_blacklist(self, entity_type: str, entity_id: int, reason: str, banned_by: int,
                         duration_hours: int = None):
        """Fügt einen User oder Server zur Blacklist hinzu"""
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
                logger.info(f"Zur Blacklist hinzugefügt: {entity_type} {entity_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Hinzufügen zur Blacklist: {e}")
            return False

    def remove_from_blacklist(self, entity_type: str, entity_id: int) -> bool:
        """Entfernt einen User oder Server von der Blacklist"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    DELETE FROM globalchat_blacklist 
                    WHERE entity_type = ? AND entity_id = ?
                """, (entity_type, entity_id))
                changes = c.rowcount
                conn.commit()

                if changes > 0:
                    logger.info(f"Von Blacklist entfernt: {entity_type} {entity_id}")
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Entfernen von der Blacklist: {e}")
            return False

    def is_blacklisted(self, entity_type: str, entity_id: int) -> bool:
        """Prüft ob ein User oder Server auf der Blacklist steht"""
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

                # Permanent ban
                if result['is_permanent']:
                    return True

                # Temporärer Ban - prüfen ob abgelaufen
                if result['expires_at']:
                    expires_at = datetime.fromisoformat(result['expires_at'])
                    if datetime.now() > expires_at:
                        # Ban abgelaufen, automatisch entfernen
                        self.remove_from_blacklist(entity_type, entity_id)
                        return False
                    return True

                return False
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Prüfen der Blacklist: {e}")
            return False

    def get_blacklist(self, entity_type: str = None) -> List[Dict]:
        """Holt die komplette Blacklist oder gefiltert nach Typ"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                if entity_type:
                    c.execute("SELECT * FROM globalchat_blacklist WHERE entity_type = ?", (entity_type,))
                else:
                    c.execute("SELECT * FROM globalchat_blacklist")
                return [dict(row) for row in c.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Abrufen der Blacklist: {e}")
            return []

    # Guild Settings
    def get_guild_settings(self, guild_id: int) -> Dict:
        """Holt die Einstellungen für eine Guild"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
                result = c.fetchone()

                if result:
                    return dict(result)
                else:
                    # Default-Einstellungen zurückgeben
                    return {
                        'guild_id': guild_id,
                        'filter_enabled': True,
                        'nsfw_filter': True,
                        'embed_color': '#5865F2',
                        'custom_webhook_name': None,
                        'max_message_length': 1900
                    }
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Abrufen der Guild-Settings: {e}")
            return {}

    def update_guild_setting(self, guild_id: int, setting_name: str, value) -> bool:
        """Aktualisiert eine Guild-Einstellung"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                # Zuerst prüfen ob Eintrag existiert
                c.execute("SELECT guild_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
                if not c.fetchone():
                    # Neuen Eintrag erstellen
                    c.execute("INSERT INTO guild_settings (guild_id) VALUES (?)", (guild_id,))

                # Setting aktualisieren
                c.execute(f"UPDATE guild_settings SET {setting_name} = ? WHERE guild_id = ?", (value, guild_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Fehler beim Aktualisieren der Guild-Settings: {e}")
            return False

    # Statistiken
    def get_global_stats(self) -> Dict:
        """Holt globale Statistiken"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Aktive Guilds
                if self._column_exists('globalchat_channels', 'is_active'):
                    c.execute("SELECT COUNT(*) as count FROM globalchat_channels WHERE is_active = 1")
                else:
                    c.execute("SELECT COUNT(*) as count FROM globalchat_channels")
                active_guilds = c.fetchone()['count']

                # Gesamte Nachrichten heute
                c.execute("SELECT total_messages FROM daily_stats WHERE date = DATE('now')")
                today_messages = c.fetchone()
                today_messages = today_messages['total_messages'] if today_messages else 0

                # Gesamte Nachrichten aller Channels
                if self._column_exists('globalchat_channels', 'message_count'):
                    c.execute("SELECT SUM(message_count) as total FROM globalchat_channels")
                    total_messages = c.fetchone()['total'] or 0
                else:
                    total_messages = 0

                # Blacklist counts
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
            logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
            return {}

    def update_daily_stats(self):
        """Aktualisiert die täglichen Statistiken"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                today = datetime.now().date()

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
            logger.error(f"Fehler beim Aktualisieren der täglichen Stats: {e}")

    # Maintenance
    def cleanup_old_data(self, days: int = 30):
        """Bereinigt alte Daten"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Alte Message-Logs löschen
                c.execute("DELETE FROM message_log WHERE timestamp < datetime('now', '-{} days')".format(days))
                deleted_messages = c.rowcount

                # Abgelaufene Blacklist-Einträge löschen
                c.execute("DELETE FROM globalchat_blacklist WHERE expires_at < datetime('now') AND is_permanent = 0")
                deleted_bans = c.rowcount

                # Alte Statistiken löschen (älter als 90 Tage)
                c.execute("DELETE FROM daily_stats WHERE date < date('now', '-90 days')")
                deleted_stats = c.rowcount

                conn.commit()
                logger.info(
                    f"Bereinigung abgeschlossen: {deleted_messages} Messages, {deleted_bans} Bans, {deleted_stats} Stats gelöscht")
        except sqlite3.Error as e:
            logger.error(f"Fehler bei der Bereinigung: {e}")


# Globale Instanz
db = GlobalChatDatabase()