# FastCoding/__init__.py - Füge diese Zeile hinzu:
# from .welcome_database import WelcomeDatabase

import sqlite3
import asyncio
from typing import Optional, Dict, Any

class WelcomeDatabase:
    def __init__(self, db_path: str = "welcome.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialisiert die Datenbank und erstellt die Tabelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
    
    async def set_welcome_channel(self, guild_id: int, channel_id: int) -> bool:
        """Setzt den Welcome Channel für einen Server"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO welcome_settings (guild_id, channel_id, updated_at)
                VALUES (?, ?, datetime('now'))
            ''', (guild_id, channel_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Fehler beim Setzen des Welcome Channels: {e}")
            return False
    
    async def set_welcome_message(self, guild_id: int, message: str) -> bool:
        """Setzt die Welcome Message für einen Server"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO welcome_settings (guild_id, welcome_message, updated_at)
                VALUES (?, ?, datetime('now'))
            ''', (guild_id, message))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Fehler beim Setzen der Welcome Message: {e}")
            return False
    
    async def update_welcome_settings(self, guild_id: int, **kwargs) -> bool:
        """Aktualisiert Welcome Einstellungen für einen Server"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Zuerst prüfen, ob ein Eintrag existiert
            cursor.execute('SELECT guild_id FROM welcome_settings WHERE guild_id = ?', (guild_id,))
            exists = cursor.fetchone()
            
            if not exists:
                # Neuen Eintrag erstellen
                cursor.execute('''
                    INSERT INTO welcome_settings (guild_id) VALUES (?)
                ''', (guild_id,))
            
            # Dynamisch die Felder aktualisieren
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
            print(f"Fehler beim Aktualisieren der Welcome Einstellungen: {e}")
            return False
    
    async def get_welcome_settings(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Holt die Welcome Einstellungen für einen Server"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM welcome_settings WHERE guild_id = ?', (guild_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            print(f"Fehler beim Abrufen der Welcome Einstellungen: {e}")
            return None
    
    async def delete_welcome_settings(self, guild_id: int) -> bool:
        """Löscht die Welcome Einstellungen für einen Server"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM welcome_settings WHERE guild_id = ?', (guild_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Fehler beim Löschen der Welcome Einstellungen: {e}")
            return False
    
    async def toggle_welcome(self, guild_id: int) -> Optional[bool]:
        """Schaltet das Welcome System ein/aus"""
        try:
            settings = await self.get_welcome_settings(guild_id)
            if not settings:
                return None
            
            new_state = not settings.get('enabled', True)
            await self.update_welcome_settings(guild_id, enabled=new_state)
            return new_state
        except Exception as e:
            print(f"Fehler beim Toggle des Welcome Systems: {e}")
            return None