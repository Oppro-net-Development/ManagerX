# Copyright (c) 2025 OPPRO.NET Network
import sqlite3
import asyncio
from typing import Optional, List, Tuple, Dict, Any
import os
import logging
import time
from collections import defaultdict
import csv
import io


class LevelSystemLogger:
    def __init__(self):
        self.logger = logging.getLogger('levelsystem')
        if not self.logger.handlers:
            handler = logging.FileHandler('data/levelsystem.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_level_up(self, user_id: int, guild_id: int, old_level: int, new_level: int):
        self.logger.info(f"User {user_id} in guild {guild_id} leveled up: {old_level} -> {new_level}")
    
    def log_xp_gain(self, user_id: int, guild_id: int, xp_gained: int, total_xp: int):
        self.logger.debug(f"User {user_id} in guild {guild_id} gained {xp_gained} XP (total: {total_xp})")
    
    def log_prestige(self, user_id: int, guild_id: int, old_level: int):
        self.logger.info(f"User {user_id} in guild {guild_id} prestiged from level {old_level}")


class AntiSpamDetector:
    def __init__(self):
        self.user_patterns = defaultdict(list)
        self.user_messages = defaultdict(list)
    
    def is_xp_farming(self, user_id: int, message_content: str, timestamp: float) -> bool:
        patterns = self.user_patterns[user_id]
        
        # Cleanup old patterns (älter als 10 Minuten)
        patterns = [(content, ts) for content, ts in patterns if timestamp - ts < 600]
        self.user_patterns[user_id] = patterns
        
        # Gleiche Nachricht in den letzten 5 Nachrichten
        recent_messages = [content for content, ts in patterns[-5:]]
        if recent_messages.count(message_content) >= 3:
            return True
        
        # Nachricht zu kurz
        if len(message_content.strip()) < 3:
            return True
            
        patterns.append((message_content, timestamp))
        return False
    
    def is_spam(self, user_id: int, current_time: float, max_messages: int = 5, time_window: int = 60) -> bool:
        messages = self.user_messages[user_id]
        messages = [t for t in messages if current_time - t < time_window]
        self.user_messages[user_id] = messages
        
        if len(messages) >= max_messages:
            return True
        
        messages.append(current_time)
        return False


class LevelDatabase:
    def __init__(self, db_path: str = "data/levelsystem.db"):
        self.db_path = db_path
        self.logger = LevelSystemLogger()
        self.anti_spam = AntiSpamDetector()
        
        # Cache für bessere Performance
        self.level_roles_cache = {}
        self.enabled_guilds_cache = set()
        self.guild_configs_cache = {}
        
        self.init_db()
        self.load_caches()

    def init_db(self):
        """Initialisiert die Datenbank und erstellt Tabellen"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
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
                last_message REAL DEFAULT 0,
                prestige_level INTEGER DEFAULT 0,
                total_xp_earned INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')

        # Level Roles Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS level_roles (
                guild_id INTEGER,
                level INTEGER,
                role_id INTEGER,
                is_temporary BOOLEAN DEFAULT FALSE,
                duration_hours INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, level, role_id)
            )
        ''')

        # Guild Settings Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                levelsystem_enabled BOOLEAN DEFAULT TRUE,
                min_xp INTEGER DEFAULT 10,
                max_xp INTEGER DEFAULT 20,
                xp_cooldown INTEGER DEFAULT 30,
                level_up_channel INTEGER DEFAULT NULL,
                webhook_url TEXT DEFAULT NULL,
                prestige_enabled BOOLEAN DEFAULT TRUE,
                prestige_min_level INTEGER DEFAULT 50
            )
        ''')

        # Channel Settings Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_settings (
                guild_id INTEGER,
                channel_id INTEGER,
                xp_multiplier REAL DEFAULT 1.0,
                is_blacklisted BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (guild_id, channel_id)
            )
        ''')

        # XP Boosts Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS xp_boosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                multiplier REAL,
                start_time REAL,
                end_time REAL,
                is_global BOOLEAN DEFAULT FALSE
            )
        ''')

        # Achievements Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                achievement_type TEXT,
                achievement_value INTEGER,
                earned_at REAL DEFAULT (datetime('now')),
                UNIQUE(guild_id, user_id, achievement_type, achievement_value)
            )
        ''')

        # Temporary Roles Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temporary_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                role_id INTEGER,
                granted_at REAL,
                expires_at REAL
            )
        ''')

        # Performance-Indizes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_guild ON user_levels(user_id, guild_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guild_xp ON user_levels(guild_id, xp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_level_roles ON level_roles(guild_id, level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_channel_settings ON channel_settings(guild_id, channel_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_xp_boosts ON xp_boosts(guild_id, start_time, end_time)')

        conn.commit()
        conn.close()

    def load_caches(self):
        """Lädt häufig verwendete Daten in den Cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Level-Rollen Cache laden
        cursor.execute('SELECT guild_id, level, role_id FROM level_roles')
        for guild_id, level, role_id in cursor.fetchall():
            if guild_id not in self.level_roles_cache:
                self.level_roles_cache[guild_id] = {}
            self.level_roles_cache[guild_id][level] = role_id
        
        # Aktivierte Server laden
        cursor.execute('SELECT guild_id FROM guild_settings WHERE levelsystem_enabled = TRUE')
        self.enabled_guilds_cache = {row[0] for row in cursor.fetchall()}
        
        # Guild-Konfigurationen laden
        cursor.execute('SELECT * FROM guild_settings')
        for row in cursor.fetchall():
            guild_id = row[0]
            self.guild_configs_cache[guild_id] = {
                'enabled': row[1],
                'min_xp': row[2],
                'max_xp': row[3],
                'cooldown': row[4],
                'level_up_channel': row[5],
                'webhook_url': row[6],
                'prestige_enabled': row[7] if len(row) > 7 else True,
                'prestige_min_level': row[8] if len(row) > 8 else 50
            }
        
        conn.close()

    def add_xp(self, user_id: int, guild_id: int, xp_amount: int, message_content: str = "") -> Tuple[bool, int]:
        """Fügt XP zu einem User hinzu mit Anti-Spam Schutz"""
        current_time = time.time()
        
        # Anti-Spam Check
        if self.anti_spam.is_spam(user_id, current_time):
            return False, 0
        
        if message_content and self.anti_spam.is_xp_farming(user_id, message_content, current_time):
            return False, 0
        
        # XP-Boost anwenden
        xp_amount = int(xp_amount * self.get_active_xp_multiplier(guild_id, user_id))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT xp, level, messages, total_xp_earned FROM user_levels 
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))

        result = cursor.fetchone()

        if result:
            current_xp, current_level, messages, total_earned = result
            new_xp = current_xp + xp_amount
            new_level = self.calculate_level(new_xp)
            new_total_earned = total_earned + xp_amount

            cursor.execute('''
                UPDATE user_levels 
                SET xp = ?, level = ?, messages = messages + 1, last_message = ?, total_xp_earned = ?
                WHERE user_id = ? AND guild_id = ?
            ''', (new_xp, new_level, current_time, new_total_earned, user_id, guild_id))

            level_up = new_level > current_level
            if level_up:
                self.logger.log_level_up(user_id, guild_id, current_level, new_level)
        else:
            new_xp = xp_amount
            new_level = self.calculate_level(new_xp)

            cursor.execute('''
                INSERT INTO user_levels (user_id, guild_id, xp, level, messages, last_message, total_xp_earned)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            ''', (user_id, guild_id, new_xp, new_level, current_time, xp_amount))

            level_up = new_level > 0

        conn.commit()
        conn.close()

        self.logger.log_xp_gain(user_id, guild_id, xp_amount, new_xp)
        
        # Achievements prüfen
        if level_up:
            self.check_achievements(user_id, guild_id, new_level)

        return level_up, new_level

    def batch_add_xp(self, updates: List[Tuple[int, int, int]]):
        """Fügt XP für mehrere User in einem Batch hinzu"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = time.time()
        
        for user_id, guild_id, xp_amount in updates:
            cursor.execute('''
                INSERT OR REPLACE INTO user_levels 
                (user_id, guild_id, xp, level, messages, last_message, total_xp_earned)
                VALUES (
                    ?, ?, 
                    COALESCE((SELECT xp FROM user_levels WHERE user_id = ? AND guild_id = ?), 0) + ?,
                    ?, -- Level wird später berechnet
                    COALESCE((SELECT messages FROM user_levels WHERE user_id = ? AND guild_id = ?), 0) + 1,
                    ?,
                    COALESCE((SELECT total_xp_earned FROM user_levels WHERE user_id = ? AND guild_id = ?), 0) + ?
                )
            ''', (user_id, guild_id, user_id, guild_id, xp_amount, 
                  self.calculate_level(xp_amount), user_id, guild_id, current_time,
                  user_id, guild_id, xp_amount))
        
        conn.commit()
        conn.close()

    def get_user_stats(self, user_id: int, guild_id: int) -> Optional[Tuple[int, int, int, int, int]]:
        """Holt erweiterte User-Statistiken"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT xp, level, messages, prestige_level, total_xp_earned 
            FROM user_levels 
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))

        result = cursor.fetchone()
        conn.close()

        if result:
            xp, level, messages, prestige, total_earned = result
            xp_needed = self.xp_for_level(level + 1) - xp
            return xp, level, messages, xp_needed, prestige, total_earned
        return None

    def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Tuple[int, int, int, int, int]]:
        """Holt die erweiterte Leaderboard für einen Server"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, xp, level, messages, prestige_level 
            FROM user_levels 
            WHERE guild_id = ? 
            ORDER BY prestige_level DESC, level DESC, xp DESC 
            LIMIT ?
        ''', (guild_id, limit))

        result = cursor.fetchall()
        conn.close()
        return result

    def get_detailed_analytics(self, guild_id: int) -> Dict[str, Any]:
        """Holt detaillierte Server-Analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = time.time()
        today_start = current_time - (current_time % 86400)  # Tagesbeginn
        week_start = current_time - (7 * 86400)  # Eine Woche zurück
        
        analytics = {}
        
        # Grundlegende Statistiken
        cursor.execute('''
            SELECT 
                COUNT(*) as total_users,
                AVG(level) as avg_level,
                MAX(level) as max_level,
                SUM(xp) as total_xp,
                SUM(messages) as total_messages
            FROM user_levels WHERE guild_id = ?
        ''', (guild_id,))
        
        result = cursor.fetchone()
        if result:
            analytics.update({
                'total_users': result[0],
                'avg_level': result[1] or 0,
                'max_level': result[2] or 0,
                'total_xp': result[3] or 0,
                'total_messages': result[4] or 0
            })
        
        # Aktivität heute (basierend auf last_message)
        cursor.execute('''
            SELECT COUNT(*) FROM user_levels 
            WHERE guild_id = ? AND last_message > ?
        ''', (guild_id, today_start))
        
        analytics['active_today'] = cursor.fetchone()[0]
        
        # XP-Verteilung
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN level BETWEEN 1 AND 10 THEN 1 END) as novice,
                COUNT(CASE WHEN level BETWEEN 11 AND 25 THEN 1 END) as intermediate,
                COUNT(CASE WHEN level BETWEEN 26 AND 50 THEN 1 END) as advanced,
                COUNT(CASE WHEN level > 50 THEN 1 END) as expert
            FROM user_levels WHERE guild_id = ?
        ''', (guild_id,))
        
        level_distribution = cursor.fetchone()
        analytics['level_distribution'] = {
            'novice': level_distribution[0],
            'intermediate': level_distribution[1],
            'advanced': level_distribution[2],
            'expert': level_distribution[3]
        }
        
        conn.close()
        return analytics

    def set_guild_config(self, guild_id: int, **config):
        """Setzt Guild-spezifische Konfiguration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Aktuelle Konfiguration holen
        cursor.execute('SELECT * FROM guild_settings WHERE guild_id = ?', (guild_id,))
        current = cursor.fetchone()
        
        if current:
            # Update bestehende Konfiguration
            set_clauses = []
            values = []
            for key, value in config.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            values.append(guild_id)
            
            query = f"UPDATE guild_settings SET {', '.join(set_clauses)} WHERE guild_id = ?"
            cursor.execute(query, values)
        else:
            # Neue Konfiguration erstellen
            keys = list(config.keys()) + ['guild_id']
            values = list(config.values()) + [guild_id]
            placeholders = ', '.join(['?'] * len(keys))
            
            query = f"INSERT INTO guild_settings ({', '.join(keys)}) VALUES ({placeholders})"
            cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        # Cache aktualisieren
        if guild_id not in self.guild_configs_cache:
            self.guild_configs_cache[guild_id] = {}
        self.guild_configs_cache[guild_id].update(config)

    def get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        """Holt Guild-Konfiguration"""
        if guild_id in self.guild_configs_cache:
            return self.guild_configs_cache[guild_id]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM guild_settings WHERE guild_id = ?', (guild_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            config = {
                'enabled': result[1],
                'min_xp': result[2],
                'max_xp': result[3],
                'cooldown': result[4],
                'level_up_channel': result[5],
                'webhook_url': result[6],
                'prestige_enabled': result[7] if len(result) > 7 else True,
                'prestige_min_level': result[8] if len(result) > 8 else 50
            }
        else:
            config = {
                'enabled': True,
                'min_xp': 10,
                'max_xp': 20,
                'cooldown': 30,
                'level_up_channel': None,
                'webhook_url': None,
                'prestige_enabled': True,
                'prestige_min_level': 50
            }
        
        self.guild_configs_cache[guild_id] = config
        return config

    def set_channel_multiplier(self, guild_id: int, channel_id: int, multiplier: float):
        """Setzt XP-Multiplikator für einen Kanal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO channel_settings (guild_id, channel_id, xp_multiplier)
            VALUES (?, ?, ?)
        ''', (guild_id, channel_id, multiplier))
        
        conn.commit()
        conn.close()

    def add_blacklisted_channel(self, guild_id: int, channel_id: int):
        """Fügt einen Kanal zur Blacklist hinzu"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO channel_settings (guild_id, channel_id, is_blacklisted)
            VALUES (?, ?, TRUE)
        ''', (guild_id, channel_id))
        
        conn.commit()
        conn.close()

    def is_channel_blacklisted(self, guild_id: int, channel_id: int) -> bool:
        """Prüft ob ein Kanal auf der Blacklist steht"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT is_blacklisted FROM channel_settings 
            WHERE guild_id = ? AND channel_id = ?
        ''', (guild_id, channel_id))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else False

    def get_channel_multiplier(self, guild_id: int, channel_id: int) -> float:
        """Holt den XP-Multiplikator für einen Kanal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT xp_multiplier FROM channel_settings 
            WHERE guild_id = ? AND channel_id = ?
        ''', (guild_id, channel_id))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 1.0

    def add_xp_boost(self, guild_id: int, user_id: Optional[int], multiplier: float, duration_hours: int):
        """Fügt einen XP-Boost hinzu"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = time.time()
        end_time = current_time + (duration_hours * 3600)
        is_global = user_id is None
        
        cursor.execute('''
            INSERT INTO xp_boosts (guild_id, user_id, multiplier, start_time, end_time, is_global)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (guild_id, user_id, multiplier, current_time, end_time, is_global))
        
        conn.commit()
        conn.close()

    def get_active_xp_multiplier(self, guild_id: int, user_id: int) -> float:
        """Holt den aktuell aktiven XP-Multiplikator für einen User"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = time.time()
        
        cursor.execute('''
            SELECT multiplier FROM xp_boosts 
            WHERE guild_id = ? AND (user_id = ? OR is_global = TRUE) 
            AND start_time <= ? AND end_time > ?
            ORDER BY multiplier DESC LIMIT 1
        ''', (guild_id, user_id, current_time, current_time))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 1.0

    def prestige_user(self, user_id: int, guild_id: int) -> bool:
        """Führt ein Prestige für einen User durch"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT level, prestige_level FROM user_levels 
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))
        
        result = cursor.fetchone()
        if not result or result[0] < self.get_guild_config(guild_id)['prestige_min_level']:
            conn.close()
            return False
        
        old_level, current_prestige = result
        
        cursor.execute('''
            UPDATE user_levels 
            SET level = 0, xp = 0, prestige_level = prestige_level + 1
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))
        
        conn.commit()
        conn.close()
        
        self.logger.log_prestige(user_id, guild_id, old_level)
        return True

    def check_achievements(self, user_id: int, guild_id: int, level: int):
        """Prüft und verleiht Achievements"""
        achievements_to_grant = []
        
        # Level-basierte Achievements
        milestone_levels = [10, 25, 50, 75, 100]
        for milestone in milestone_levels:
            if level >= milestone:
                achievements_to_grant.append(('level_milestone', milestone))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for achievement_type, value in achievements_to_grant:
            cursor.execute('''
                INSERT OR IGNORE INTO achievements (guild_id, user_id, achievement_type, achievement_value)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, user_id, achievement_type, value))
        
        conn.commit()
        conn.close()

    def export_guild_data(self, guild_id: int) -> List[Tuple]:
        """Exportiert alle Guild-Daten"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, xp, level, messages, prestige_level, total_xp_earned
            FROM user_levels WHERE guild_id = ?
            ORDER BY prestige_level DESC, level DESC, xp DESC
        ''', (guild_id,))
        
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
                u1.prestige_level > (SELECT prestige_level FROM user_levels WHERE user_id = ? AND guild_id = ?) OR
                (u1.prestige_level = (SELECT prestige_level FROM user_levels WHERE user_id = ? AND guild_id = ?) AND
                 u1.level > (SELECT level FROM user_levels WHERE user_id = ? AND guild_id = ?)) OR
                (u1.prestige_level = (SELECT prestige_level FROM user_levels WHERE user_id = ? AND guild_id = ?) AND
                 u1.level = (SELECT level FROM user_levels WHERE user_id = ? AND guild_id = ?) AND 
                 u1.xp > (SELECT xp FROM user_levels WHERE user_id = ? AND guild_id = ?))
            )
        ''', (guild_id, user_id, guild_id, user_id, guild_id, user_id, guild_id, 
              user_id, guild_id, user_id, guild_id, user_id, guild_id))

        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def add_level_role(self, guild_id: int, level: int, role_id: int, is_temporary: bool = False, duration_hours: int = 0):
        """Fügt eine Level-Rolle hinzu"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO level_roles (guild_id, level, role_id, is_temporary, duration_hours)
            VALUES (?, ?, ?, ?, ?)
        ''', (guild_id, level, role_id, is_temporary, duration_hours))

        conn.commit()
        conn.close()
        
        # Cache aktualisieren
        if guild_id not in self.level_roles_cache:
            self.level_roles_cache[guild_id] = {}
        self.level_roles_cache[guild_id][level] = role_id

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
        
        # Cache aktualisieren
        if guild_id in self.level_roles_cache and level in self.level_roles_cache[guild_id]:
            del self.level_roles_cache[guild_id][level]

    def get_level_roles(self, guild_id: int) -> List[Tuple[int, int, bool, int]]:
        """Holt alle Level-Rollen für einen Server"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT level, role_id, is_temporary, duration_hours FROM level_roles 
            WHERE guild_id = ? 
            ORDER BY level ASC
        ''', (guild_id,))

        result = cursor.fetchall()
        conn.close()
        return result

    def get_role_for_level(self, guild_id: int, level: int) -> Optional[int]:
        """Holt die Rolle für ein bestimmtes Level aus Cache"""
        if guild_id in self.level_roles_cache:
            # Finde die höchste Rolle <= level
            applicable_roles = {l: r for l, r in self.level_roles_cache[guild_id].items() if l <= level}
            if applicable_roles:
                highest_level = max(applicable_roles.keys())
                return applicable_roles[highest_level]
        return None

    def set_levelsystem_enabled(self, guild_id: int, enabled: bool):
        """Aktiviert/Deaktiviert das Levelsystem für einen Server"""
        self.set_guild_config(guild_id, levelsystem_enabled=enabled)
        
        # Cache aktualisieren
        if enabled:
            self.enabled_guilds_cache.add(guild_id)
        else:
            self.enabled_guilds_cache.discard(guild_id)

    def is_levelsystem_enabled(self, guild_id: int) -> bool:
        """Prüft ob das Levelsystem für einen Server aktiviert ist (aus Cache)"""
        if guild_id in self.enabled_guilds_cache:
            return True
        
        # Fallback zur Datenbank wenn nicht im Cache
        config = self.get_guild_config(guild_id)
        enabled = config.get('enabled', True)
        
        if enabled:
            self.enabled_guilds_cache.add(guild_id)
        
        return enabled

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
