"""
Welcome Database Handler
=========================

Datenbank-Handler für das Welcome System mit vollständiger
Rückwärtskompatibilität und automatischer Migration.

Copyright (c) 2025 OPPRO.NET Network
"""

import sqlite3
import aiosqlite
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Logger Setup
logger = logging.getLogger(__name__)


class WelcomeDatabase:
    """
    Datenbank-Handler für Welcome System Einstellungen.
    
    Bietet synchrone und asynchrone Methoden mit automatischer
    Fallback-Logik für Rückwärtskompatibilität. Unterstützt
    automatische Datenbankmigrationen.
    
    Parameters
    ----------
    db_path : str, optional
        Pfad zur SQLite-Datenbank, by default "data/welcome.db"
    
    Attributes
    ----------
    db_path : str
        Pfad zur SQLite-Datenbank
    migration_done : bool
        Status der Datenbankmigrierung
    
    Examples
    --------
    >>> db = WelcomeDatabase()
    >>> await db.update_welcome_settings(123456, channel_id=789012)
    True
    """
    
    def __init__(self, db_path: str = "data/welcome.db"):
        """
        Initialisiert den Datenbank-Handler.
        
        Parameters
        ----------
        db_path : str, optional
            Pfad zur SQLite-Datenbank, by default "data/welcome.db"
        
        Notes
        -----
        Erstellt automatisch die Basis-Tabellen wenn sie nicht existieren.
        """
        self.db_path = db_path
        self.migration_done = False
        self.init_database()
    
    def init_database(self):
        """
        Initialisiert die Datenbank synchron für Rückwärtskompatibilität.
        
        Notes
        -----
        Erstellt die Basis-Tabelle `welcome_settings` mit allen
        ursprünglichen Feldern. Neue Felder werden später durch
        `migrate_database()` hinzugefügt.
        
        Diese Methode ist synchron um Kompatibilität mit älteren
        Versionen zu gewährleisten.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Basis-Tabelle erstellen (alte Version)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS welcome_settings (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                welcome_message TEXT,
                enabled INTEGER DEFAULT 1,
                embed_enabled INTEGER DEFAULT 0,
                embed_color TEXT DEFAULT '#00ff00',
                embed_title TEXT,
                embed_description TEXT,
                embed_thumbnail INTEGER DEFAULT 0,
                embed_footer TEXT,
                ping_user INTEGER DEFAULT 0,
                delete_after INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def migrate_database(self):
        """
        Migriert die Datenbank zu neuen Features (async).
        
        Notes
        -----
        Fügt folgende neue Spalten hinzu:
        - auto_role_id: Automatische Rollenvergabe
        - join_dm_enabled: Private Willkommensnachrichten
        - join_dm_message: DM Nachrichtentext
        - template_name: Verwendete Vorlage
        - welcome_stats_enabled: Statistik-Tracking
        - rate_limit_enabled: Rate-Limiting aktiv
        - rate_limit_seconds: Rate-Limit Zeitfenster
        
        Erstellt außerdem die `welcome_stats` Tabelle für Statistiken.
        
        Die Migrierung wird nur einmal pro Instanz ausgeführt.
        """
        if self.migration_done:
            return
        
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                # Prüfe welche Spalten bereits existieren
                cursor = await conn.execute("PRAGMA table_info(welcome_settings)")
                columns = await cursor.fetchall()
                existing_columns = [col[1] for col in columns]
                
                # Neue Spalten hinzufügen falls nicht vorhanden
                new_columns = {
                    'auto_role_id': 'INTEGER',
                    'join_dm_enabled': 'INTEGER DEFAULT 0',
                    'join_dm_message': 'TEXT',
                    'template_name': 'TEXT',
                    'welcome_stats_enabled': 'INTEGER DEFAULT 0',
                    'rate_limit_enabled': 'INTEGER DEFAULT 1',
                    'rate_limit_seconds': 'INTEGER DEFAULT 60'
                }
                
                for column_name, column_def in new_columns.items():
                    if column_name not in existing_columns:
                        try:
                            await conn.execute(f'ALTER TABLE welcome_settings ADD COLUMN {column_name} {column_def}')
                            logger.info(f"Spalte {column_name} hinzugefügt")
                        except sqlite3.OperationalError:
                            # Spalte existiert bereits
                            pass
                
                # Neue Tabelle für Statistiken
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS welcome_stats (
                        guild_id INTEGER,
                        date TEXT,
                        joins INTEGER DEFAULT 0,
                        leaves INTEGER DEFAULT 0,
                        PRIMARY KEY (guild_id, date)
                    )
                ''')
                
                await conn.commit()
                self.migration_done = True
                logger.info("Datenbankmigrierung abgeschlossen")
                
        except Exception as e:
            logger.error(f"Fehler bei Datenbankmigrierung: {e}")
    
    async def set_welcome_channel(self, guild_id: int, channel_id: int) -> bool:
        """
        Setzt den Welcome Channel (Rückwärtskompatible Methode).
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        channel_id : int
            Discord Channel ID
        
        Returns
        -------
        bool
            True bei Erfolg, False bei Fehler
        
        Notes
        -----
        Diese Methode ist deprecated, verwende stattdessen
        `update_welcome_settings(guild_id, channel_id=channel_id)`.
        """
        return await self.update_welcome_settings(guild_id, channel_id=channel_id)
    
    async def set_welcome_message(self, guild_id: int, message: str) -> bool:
        """
        Setzt die Welcome Message (Rückwärtskompatible Methode).
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        message : str
            Welcome Message Text
        
        Returns
        -------
        bool
            True bei Erfolg, False bei Fehler
        
        Notes
        -----
        Diese Methode ist deprecated, verwende stattdessen
        `update_welcome_settings(guild_id, welcome_message=message)`.
        """
        return await self.update_welcome_settings(guild_id, welcome_message=message)
    
    async def update_welcome_settings(self, guild_id: int, **kwargs) -> bool:
        """
        Aktualisiert Welcome Einstellungen mit Fallback auf sync.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        **kwargs : dict
            Felder zum Aktualisieren (siehe Notes)
        
        Returns
        -------
        bool
            True bei Erfolg, False bei Fehler
        
        Notes
        -----
        Gültige Felder in kwargs:
        - channel_id : int
        - welcome_message : str
        - enabled : bool/int
        - embed_enabled : bool/int
        - embed_color : str (Hex-Format)
        - embed_title : str
        - embed_description : str
        - embed_thumbnail : bool/int
        - embed_footer : str
        - ping_user : bool/int
        - delete_after : int (Sekunden)
        - auto_role_id : int
        - join_dm_enabled : bool/int
        - join_dm_message : str
        - template_name : str
        - welcome_stats_enabled : bool/int
        - rate_limit_enabled : bool/int
        - rate_limit_seconds : int
        
        Erstellt automatisch einen neuen Eintrag wenn keiner existiert.
        Bei async-Fehlern wird automatisch auf sync Fallback gewechselt.
        
        Examples
        --------
        >>> await db.update_welcome_settings(
        ...     123456,
        ...     channel_id=789012,
        ...     welcome_message="Willkommen %mention%!",
        ...     embed_enabled=True
        ... )
        True
        """
        try:
            await self.migrate_database()
            
            async with aiosqlite.connect(self.db_path) as conn:
                # Prüfen ob Eintrag existiert
                cursor = await conn.execute('SELECT guild_id FROM welcome_settings WHERE guild_id = ?', (guild_id,))
                exists = await cursor.fetchone()
                
                if not exists:
                    # Neuen Eintrag erstellen
                    await conn.execute('''
                        INSERT INTO welcome_settings (guild_id) VALUES (?)
                    ''', (guild_id,))
                
                # Dynamisch die Felder aktualisieren
                valid_fields = [
                    'channel_id', 'welcome_message', 'enabled', 'embed_enabled',
                    'embed_color', 'embed_title', 'embed_description', 'embed_thumbnail',
                    'embed_footer', 'ping_user', 'delete_after', 'auto_role_id',
                    'join_dm_enabled', 'join_dm_message', 'template_name',
                    'welcome_stats_enabled', 'rate_limit_enabled', 'rate_limit_seconds'
                ]
                
                update_fields = []
                values = []
                
                for key, value in kwargs.items():
                    if key in valid_fields:
                        update_fields.append(f"{key} = ?")
                        values.append(value)
                
                if update_fields:
                    update_fields.append("updated_at = datetime('now')")
                    query = f"UPDATE welcome_settings SET {', '.join(update_fields)} WHERE guild_id = ?"
                    values.append(guild_id)
                    await conn.execute(query, values)
                
                await conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Async Update fehlgeschlagen, verwende Sync Fallback: {e}")
            # Fallback auf synchrone Version
            return self._sync_update_welcome_settings(guild_id, **kwargs)
    
    def _sync_update_welcome_settings(self, guild_id: int, **kwargs) -> bool:
        """
        Sync Fallback für alte Versionen.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        **kwargs : dict
            Felder zum Aktualisieren
        
        Returns
        -------
        bool
            True bei Erfolg, False bei Fehler
        
        Notes
        -----
        Unterstützt nur Basis-Felder für Rückwärtskompatibilität.
        Neue Felder werden ignoriert.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT guild_id FROM welcome_settings WHERE guild_id = ?', (guild_id,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute('INSERT INTO welcome_settings (guild_id) VALUES (?)', (guild_id,))
            
            # Nur bekannte Felder für Rückwärtskompatibilität
            valid_fields = [
                'channel_id', 'welcome_message', 'enabled', 'embed_enabled',
                'embed_color', 'embed_title', 'embed_description', 'embed_thumbnail',
                'embed_footer', 'ping_user', 'delete_after'
            ]
            
            update_fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in valid_fields:
                    update_fields.append(f"{key} = ?")
                    values.append(value)
            
            if update_fields:
                update_fields.append("updated_at = datetime('now')")
                query = f"UPDATE welcome_settings SET {', '.join(update_fields)} WHERE guild_id = ?"
                values.append(guild_id)
                cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Sync Update Fehler: {e}")
            return False
    
    async def get_welcome_settings(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """
        Holt Welcome Einstellungen mit sync Fallback.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        
        Returns
        -------
        dict or None
            Dictionary mit allen Einstellungen oder None wenn nicht vorhanden
        
        Notes
        -----
        Gibt ein Dictionary zurück mit allen Feldern als Keys.
        Bei async-Fehlern wird automatisch auf sync Fallback gewechselt.
        
        Examples
        --------
        >>> settings = await db.get_welcome_settings(123456)
        >>> if settings:
        ...     print(settings['channel_id'])
        ...     print(settings['welcome_message'])
        """
        try:
            await self.migrate_database()
            
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute('SELECT * FROM welcome_settings WHERE guild_id = ?', (guild_id,))
                result = await cursor.fetchone()
                
                if result:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, result))
                return None
                
        except Exception as e:
            logger.error(f"Async Get fehlgeschlagen, verwende Sync Fallback: {e}")
            return self._sync_get_welcome_settings(guild_id)
    
    def _sync_get_welcome_settings(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """
        Sync Fallback für Einstellungen holen.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        
        Returns
        -------
        dict or None
            Dictionary mit Einstellungen oder None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM welcome_settings WHERE guild_id = ?', (guild_id,))
            result = cursor.fetchone()
            
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Sync Get Fehler: {e}")
            return None
    
    async def delete_welcome_settings(self, guild_id: int) -> bool:
        """
        Löscht alle Welcome Einstellungen für einen Server.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        
        Returns
        -------
        bool
            True bei Erfolg, False bei Fehler
        
        Notes
        -----
        Löscht nur die Einstellungen, nicht die Statistiken.
        Diese Aktion kann nicht rückgängig gemacht werden.
        """
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('DELETE FROM welcome_settings WHERE guild_id = ?', (guild_id,))
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen: {e}")
            return False
    
    async def toggle_welcome(self, guild_id: int) -> Optional[bool]:
        """
        Schaltet das Welcome System ein/aus.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        
        Returns
        -------
        bool or None
            Neuer Status (True=aktiviert, False=deaktiviert)
            oder None wenn keine Einstellungen vorhanden
        
        Examples
        --------
        >>> new_state = await db.toggle_welcome(123456)
        >>> if new_state is not None:
        ...     print(f"Welcome System ist jetzt {'aktiviert' if new_state else 'deaktiviert'}")
        """
        try:
            settings = await self.get_welcome_settings(guild_id)
            if not settings:
                return None
            
            new_state = not settings.get('enabled', True)
            await self.update_welcome_settings(guild_id, enabled=new_state)
            return new_state
        except Exception as e:
            logger.error(f"Toggle Fehler: {e}")
            return None
    
    async def update_welcome_stats(self, guild_id: int, joins: int = 0, leaves: int = 0):
        """
        Aktualisiert Welcome Statistiken für den aktuellen Tag.
        
        Parameters
        ----------
        guild_id : int
            Discord Server ID
        joins : int, optional
            Anzahl neuer Beitritte hinzuzufügen, by default 0
        leaves : int, optional
            Anzahl Austritte hinzuzufügen, by default 0
        
        Notes
        -----
        Verwendet das aktuelle Datum als Schlüssel.
        Summiert die Werte wenn bereits Einträge für heute existieren.
        Erstellt automatisch einen neuen Eintrag wenn keiner vorhanden ist.
        
        Die Statistiken werden in der `welcome_stats` Tabelle gespeichert
        mit einer Zeile pro Server pro Tag.
        
        Examples
        --------
        >>> # Einen neuen Join tracken
        >>> await db.update_welcome_stats(123456, joins=1)
        >>> 
        >>> # Einen Leave tracken
        >>> await db.update_welcome_stats(123456, leaves=1)
        """
        try:
            await self.migrate_database()
            date = datetime.now().strftime('%Y-%m-%d')
            
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('''
                    INSERT OR REPLACE INTO welcome_stats (guild_id, date, joins, leaves)
                    VALUES (?, ?, 
                        COALESCE((SELECT joins FROM welcome_stats WHERE guild_id = ? AND date = ?), 0) + ?,
                        COALESCE((SELECT leaves FROM welcome_stats WHERE guild_id = ? AND date = ?), 0) + ?)
                ''', (guild_id, date, guild_id, date, joins, guild_id, date, leaves))
                await conn.commit()
        except Exception as e:
            logger.error(f"Stats Update Fehler: {e}")