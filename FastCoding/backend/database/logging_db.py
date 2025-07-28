# Copyright (c) 2025 OPPRO.NET Network
import sqlite3
import asyncio
from typing import Optional, Dict


class LoggingDatabase:
    def __init__(self, db_path: str = "data/log_channels.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Erstellt die einfache Tabelle für Log-Channels"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS log_channels (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    log_type TEXT DEFAULT 'default'  -- neue Spalte für log_type
                )
            ''')
            conn.commit()

    async def set_log_channel(self, guild_id: int, channel_id: int, log_type: str = 'default'):
        def _insert():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO log_channels (guild_id, channel_id, enabled, log_type)
                    VALUES (?, ?, ?, ?)
                ''', (guild_id, channel_id, True, log_type))
                conn.commit()

        await asyncio.get_event_loop().run_in_executor(None, _insert)

        await asyncio.get_event_loop().run_in_executor(None, _insert)

    async def get_log_channel(self, guild_id: int) -> Optional[int]:
        """Holt die Channel-ID für einen Server"""

        def _select():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT channel_id FROM log_channels 
                    WHERE guild_id = ? AND enabled = 1
                ''', (guild_id,))
                row = cursor.fetchone()
                return row[0] if row else None

        return await asyncio.get_event_loop().run_in_executor(None, _select)

    async def disable_logging(self, guild_id: int):
        """Deaktiviert das Logging für einen Server"""

        def _update():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE log_channels SET enabled = 0 WHERE guild_id = ?
                ''', (guild_id,))
                conn.commit()

        await asyncio.get_event_loop().run_in_executor(None, _update)

    async def remove_log_channel(self, guild_id: int):
        """Entfernt den Log-Channel für einen Server komplett"""

        def _delete():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM log_channels WHERE guild_id = ?
                ''', (guild_id,))
                conn.commit()

        await asyncio.get_event_loop().run_in_executor(None, _delete)