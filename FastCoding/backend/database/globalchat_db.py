import sqlite3
import os
import logging
from typing import Optional, List

# Logger
logger = logging.getLogger(__name__)

DB_PATH = "data/globalchat.db"


def _ensure_db_dir():
    """Stellt sicher dass das data-Verzeichnis existiert"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _get_connection():
    """Gibt eine Datenbankverbindung zurück"""
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    return conn


def create_tables():
    """Erstellt die Datenbanktabellen"""
    try:
        with _get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS globalchat_channels (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            logger.info("Datenbanktabellen erstellt")
    except sqlite3.Error as e:
        logger.error(f"Fehler beim Erstellen der Tabellen: {e}")
        raise


def set_globalchat_channel(guild_id: int, channel_id: int) -> bool:
    """Setzt einen GlobalChat-Channel für eine Guild"""
    try:
        with _get_connection() as conn:
            c = conn.cursor()
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


def get_all_channels() -> List[int]:
    """Gibt alle aktiven GlobalChat-Channel-IDs zurück"""
    try:
        with _get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT channel_id FROM globalchat_channels")
            result = [row[0] for row in c.fetchall()]
            logger.debug(f"Alle Channels abgerufen: {len(result)} aktive Channels")
            return result
    except sqlite3.Error as e:
        logger.error(f"Fehler beim Abrufen aller Channels: {e}")
        return []


def get_globalchat_channel(guild_id: int) -> Optional[int]:
    """Gibt die Channel-ID für eine Guild zurück"""
    try:
        with _get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT channel_id FROM globalchat_channels 
                WHERE guild_id = ?
            """, (guild_id,))
            result = c.fetchone()
            return result[0] if result else None
    except sqlite3.Error as e:
        logger.error(f"Fehler beim Abrufen des Channels für Guild {guild_id}: {e}")
        return None


def remove_globalchat_channel(guild_id: int) -> bool:
    """Entfernt einen GlobalChat-Channel"""
    try:
        with _get_connection() as conn:
            c = conn.cursor()
            # Richtig löschen
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


def get_total_stats() -> dict:
    """Gibt einfache Statistiken zurück"""
    try:
        with _get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT 
                    COUNT(*) as total_guilds
                FROM globalchat_channels
            """)
            result = c.fetchone()
            return {
                'total_guilds': result[0]
            }
    except sqlite3.Error as e:
        logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
        return {'total_guilds': 0}


def cleanup_old_inactive(days: int = 30):
    """Löscht alte inaktive Channels nach X Tagen"""
    try:
        with _get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                DELETE FROM globalchat_channels 
                WHERE is_active = 0 
                AND created_at < datetime('now', '-{} days')
            """.format(days))
            deleted = c.rowcount
            conn.commit()

            if deleted > 0:
                logger.info(f"Bereinigte {deleted} alte Channel-Einträge")
    except sqlite3.Error as e:
        logger.error(f"Fehler beim Bereinigen: {e}")


# Alias für Kompatibilität
get_channel_for_guild = get_globalchat_channel