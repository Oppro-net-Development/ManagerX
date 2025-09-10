# OPPRO.NET Network

import sqlite3
import aiosqlite
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Logger Setup
logger = logging.getLogger(__name__)

class WelcomeDatabase:
    def __init__(self, db_path: str = "welcome.db"):
        self.db_path = db_path
        self.migration_done = False
        self.init_database()
    
    def init_database(self):
        """Initialisiert die Datenbank synchron für Rückwärtskompatibilität"""
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
        """Migriert die Datenbank zu neuen Features (async)"""
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
        """Rückwärtskompatible Methode"""
        return await self.update_welcome_settings(guild_id, channel_id=channel_id)
    
    async def set_welcome_message(self, guild_id: int, message: str) -> bool:
        """Rückwärtskompatible Methode"""
        return await self.update_welcome_settings(guild_id, welcome_message=message)
    
    async def update_welcome_settings(self, guild_id: int, **kwargs) -> bool:
        """Async Update mit Fallback auf sync"""
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
        """Sync Fallback für alte Versionen"""
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
        """Async Get mit sync Fallback"""
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
        """Sync Fallback"""
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
        """Löscht Welcome Einstellungen"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('DELETE FROM welcome_settings WHERE guild_id = ?', (guild_id,))
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen: {e}")
            return False
    
    async def toggle_welcome(self, guild_id: int) -> Optional[bool]:
        """Toggle Welcome System"""
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
        """Aktualisiert Welcome Statistiken"""
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
