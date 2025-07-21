# Copyright (c) 2025 OPPRO.NET Network
import sqlite3
import asyncio
from typing import Optional, List, Tuple
import os


class LevelDatabase:
    def __init__(self, db_path: str = "data/levelsystem.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialisiert die Datenbank und erstellt Tabellen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # User Levels Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_levels (
                user_id INTEGER,
                guild_id INTEGER,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                messages INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')

        # Level Roles Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS level_roles (
                guild_id INTEGER,
                level INTEGER,
                role_id INTEGER,
                PRIMARY KEY (guild_id, level)
            )
        ''')

        # Guild Settings Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                levelsystem_enabled BOOLEAN DEFAULT TRUE,
                xp_per_message INTEGER DEFAULT 15,
                xp_cooldown INTEGER DEFAULT 60
            )
        ''')

        conn.commit()
        conn.close()

    def add_xp(self, user_id: int, guild_id: int, xp_amount: int):
        """Fügt XP zu einem User hinzu"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # User existiert bereits?
        cursor.execute('''
            SELECT xp, level, messages FROM user_levels 
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))

        result = cursor.fetchone()

        if result:
            current_xp, current_level, messages = result
            new_xp = current_xp + xp_amount
            new_level = self.calculate_level(new_xp)

            cursor.execute('''
                UPDATE user_levels 
                SET xp = ?, level = ?, messages = messages + 1
                WHERE user_id = ? AND guild_id = ?
            ''', (new_xp, new_level, user_id, guild_id))

            level_up = new_level > current_level
        else:
            new_xp = xp_amount
            new_level = self.calculate_level(new_xp)

            cursor.execute('''
                INSERT INTO user_levels (user_id, guild_id, xp, level, messages)
                VALUES (?, ?, ?, ?, 1)
            ''', (user_id, guild_id, new_xp, new_level))

            level_up = new_level > 0

        conn.commit()
        conn.close()

        return level_up, new_level

    def get_user_stats(self, user_id: int, guild_id: int) -> Optional[Tuple[int, int, int, int]]:
        """Holt User-Statistiken"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT xp, level, messages FROM user_levels 
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))

        result = cursor.fetchone()
        conn.close()

        if result:
            xp, level, messages = result
            xp_needed = self.xp_for_level(level + 1) - xp
            return xp, level, messages, xp_needed
        return None

    def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Tuple[int, int, int, int]]:
        """Holt die Leaderboard für einen Server"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, xp, level, messages 
            FROM user_levels 
            WHERE guild_id = ? 
            ORDER BY level DESC, xp DESC 
            LIMIT ?
        ''', (guild_id, limit))

        result = cursor.fetchall()
        conn.close()
        return result

    def get_user_rank(self, user_id: int, guild_id: int) -> int:
        """Holt den Rang eines Users auf dem Server"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) + 1 as rank
            FROM user_levels u1
            WHERE u1.guild_id = ? AND (
                u1.level > (SELECT level FROM user_levels WHERE user_id = ? AND guild_id = ?) OR
                (u1.level = (SELECT level FROM user_levels WHERE user_id = ? AND guild_id = ?) AND 
                 u1.xp > (SELECT xp FROM user_levels WHERE user_id = ? AND guild_id = ?))
            )
        ''', (guild_id, user_id, guild_id, user_id, guild_id, user_id, guild_id))

        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def add_level_role(self, guild_id: int, level: int, role_id: int):
        """Fügt eine Level-Rolle hinzu"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO level_roles (guild_id, level, role_id)
            VALUES (?, ?, ?)
        ''', (guild_id, level, role_id))

        conn.commit()
        conn.close()

    def remove_level_role(self, guild_id: int, level: int):
        """Entfernt eine Level-Rolle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM level_roles 
            WHERE guild_id = ? AND level = ?
        ''', (guild_id, level))

        conn.commit()
        conn.close()

    def get_level_roles(self, guild_id: int) -> List[Tuple[int, int]]:
        """Holt alle Level-Rollen für einen Server"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT level, role_id FROM level_roles 
            WHERE guild_id = ? 
            ORDER BY level ASC
        ''', (guild_id,))

        result = cursor.fetchall()
        conn.close()
        return result

    def get_role_for_level(self, guild_id: int, level: int) -> Optional[int]:
        """Holt die Rolle für ein bestimmtes Level"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT role_id FROM level_roles 
            WHERE guild_id = ? AND level <= ?
            ORDER BY level DESC LIMIT 1
        ''', (guild_id, level))

        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def set_levelsystem_enabled(self, guild_id: int, enabled: bool):
        """Aktiviert/Deaktiviert das Levelsystem für einen Server"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO guild_settings (guild_id, levelsystem_enabled)
            VALUES (?, ?)
        ''', (guild_id, enabled))

        conn.commit()
        conn.close()

    def is_levelsystem_enabled(self, guild_id: int) -> bool:
        """Prüft ob das Levelsystem für einen Server aktiviert ist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT levelsystem_enabled FROM guild_settings 
            WHERE guild_id = ?
        ''', (guild_id,))

        result = cursor.fetchone()
        conn.close()
        return result[0] if result else True

    @staticmethod
    def calculate_level(xp: int) -> int:
        """Berechnet das Level basierend auf XP"""
        level = 0
        while xp >= LevelDatabase.xp_for_level(level + 1):
            level += 1
        return level

    @staticmethod
    def xp_for_level(level: int) -> int:
        """Berechnet die benötigten XP für ein Level"""
        if level == 0:
            return 0
        return int(100 * (level ** 1.5))