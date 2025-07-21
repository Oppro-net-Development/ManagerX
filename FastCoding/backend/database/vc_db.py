# Copyright (c) 2025 OPPRO.NET Network
import sqlite3
import os
from typing import Optional, Tuple
from colorama import Fore, Style
class TempVCDatabase:
    def __init__(self, db_path: str = "data/tempvc.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()


    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tempvc_settings (
                guild_id INTEGER PRIMARY KEY,
                creator_channel_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                auto_delete_time INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temp_channels (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def set_tempvc_settings(self, guild_id: int, creator_channel_id: int, category_id: int, auto_delete_time: int = 0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tempvc_settings 
            (guild_id, creator_channel_id, category_id, auto_delete_time) 
            VALUES (?, ?, ?, ?)
        ''', (guild_id, creator_channel_id, category_id, auto_delete_time))
        conn.commit()
        conn.close()

    def get_tempvc_settings(self, guild_id: int) -> Optional[Tuple[int, int, int]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT creator_channel_id, category_id, auto_delete_time 
            FROM tempvc_settings 
            WHERE guild_id = ?
        ''', (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def remove_tempvc_settings(self, guild_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tempvc_settings WHERE guild_id = ?', (guild_id,))
        cursor.execute('DELETE FROM temp_channels WHERE guild_id = ?', (guild_id,))
        conn.commit()
        conn.close()

    def add_temp_channel(self, channel_id: int, guild_id: int, owner_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO temp_channels (channel_id, guild_id, owner_id) 
            VALUES (?, ?, ?)
        ''', (channel_id, guild_id, owner_id))
        conn.commit()
        conn.close()

    def remove_temp_channel(self, channel_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM temp_channels WHERE channel_id = ?', (channel_id,))
        conn.commit()
        conn.close()

    def is_temp_channel(self, channel_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM temp_channels WHERE channel_id = ?', (channel_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_temp_channel_owner(self, channel_id: int) -> Optional[int]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT owner_id FROM temp_channels WHERE channel_id = ?', (channel_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_all_temp_channels(self, guild_id: int) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT channel_id, owner_id, created_at 
            FROM temp_channels 
            WHERE guild_id = ?
        ''', (guild_id,))
        result = cursor.fetchall()
        conn.close()
        return result

    def update_channel_activity(self, channel_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE temp_channels 
            SET last_activity = CURRENT_TIMESTAMP 
            WHERE channel_id = ?
        ''', (channel_id,))
        conn.commit()
        conn.close()

    def get_channels_to_delete(self, guild_id: int, minutes_inactive: int) -> list:
        if minutes_inactive <= 0:
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT channel_id FROM temp_channels 
            WHERE guild_id = ? 
            AND datetime(last_activity, '+{minutes_inactive} minutes') < datetime('now')
        ''', (guild_id,))
        result = [row[0] for row in cursor.fetchall()]
        conn.close()
        return result
