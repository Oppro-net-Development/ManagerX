# Copyright (c) 2025 OPPRO.NET Network
import sqlite3
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class StatsDB:
    """Enhanced database handler for Discord bot statistics with global level system."""

    def __init__(self, db_file="data/stats.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = asyncio.Lock()
        self._create_tables()

    def _create_tables(self):
        """Create all necessary tables for enhanced stats tracking."""
        tables = [
            '''CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                word_count INTEGER DEFAULT 0,
                has_attachment BOOLEAN DEFAULT FALSE,
                message_type TEXT DEFAULT 'text'
            )''',

            '''CREATE TABLE IF NOT EXISTS voice_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME,
                duration_minutes REAL DEFAULT 0
            )''',

            '''CREATE TABLE IF NOT EXISTS global_user_levels (
                user_id INTEGER PRIMARY KEY,
                global_level INTEGER DEFAULT 1,
                global_xp INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                total_voice_minutes INTEGER DEFAULT 0,
                total_servers INTEGER DEFAULT 0,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                achievements TEXT DEFAULT '[]',
                daily_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                last_daily_activity DATE
            )''',

            '''CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                date DATE NOT NULL,
                messages_count INTEGER DEFAULT 0,
                voice_minutes REAL DEFAULT 0,
                active_hours INTEGER DEFAULT 0,
                UNIQUE(user_id, guild_id, date)
            )''',

            '''CREATE TABLE IF NOT EXISTS channel_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                date DATE NOT NULL,
                total_messages INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                avg_words_per_message REAL DEFAULT 0,
                UNIQUE(channel_id, date)
            )''',

            '''CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_name TEXT NOT NULL,
                unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                icon TEXT DEFAULT '🏆'
            )''',

            '''CREATE TABLE IF NOT EXISTS active_voice_sessions (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )'''
        ]

        for table_sql in tables:
            self.cursor.execute(table_sql)

        # Create indexes for better performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_messages_user_timestamp ON messages(user_id, timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_messages_channel_timestamp ON messages(channel_id, timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_voice_user_timestamp ON voice_sessions(user_id, start_time)',
            'CREATE INDEX IF NOT EXISTS idx_daily_stats_user_date ON daily_stats(user_id, date)',
            'CREATE INDEX IF NOT EXISTS idx_global_levels_xp ON global_user_levels(global_xp DESC)'
        ]

        for index_sql in indexes:
            self.cursor.execute(index_sql)

        self.conn.commit()
        logger.info("Enhanced Stats database initialized")

    async def log_message(self, user_id: int, guild_id: int, channel_id: int, message_id: int,
                          word_count: int = 0, has_attachment: bool = False, message_type: str = 'text'):
        """Log a message and update global XP."""
        async with self.lock:
            try:
                # Insert message
                self.cursor.execute('''
                    INSERT INTO messages (user_id, guild_id, channel_id, message_id, word_count, has_attachment, message_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, guild_id, channel_id, message_id, word_count, has_attachment, message_type))

                # Update daily stats
                today = datetime.now().date()
                self.cursor.execute('''
                    INSERT OR IGNORE INTO daily_stats (user_id, guild_id, date, messages_count)
                    VALUES (?, ?, ?, 1)
                ''', (user_id, guild_id, today))

                self.cursor.execute('''
                    UPDATE daily_stats SET messages_count = messages_count + 1
                    WHERE user_id = ? AND guild_id = ? AND date = ?
                ''', (user_id, guild_id, today))

                # Update global level system
                await self._update_global_xp(user_id, guild_id, 'message', word_count)

                self.conn.commit()

            except Exception as e:
                logger.error(f"Error logging message: {e}")
                self.conn.rollback()

    async def start_voice_session(self, user_id: int, guild_id: int, channel_id: int):
        """Start a voice session."""
        async with self.lock:
            try:
                # End any existing session first
                await self._end_existing_voice_session(user_id)

                # Start new session
                self.cursor.execute('''
                    INSERT INTO active_voice_sessions (user_id, guild_id, channel_id)
                    VALUES (?, ?, ?)
                ''', (user_id, guild_id, channel_id))

                self.conn.commit()

            except Exception as e:
                logger.error(f"Error starting voice session: {e}")
                self.conn.rollback()

    async def end_voice_session(self, user_id: int, channel_id: int):
        """End a voice session and calculate duration."""
        async with self.lock:
            try:
                # Get active session
                self.cursor.execute('''
                    SELECT guild_id, channel_id, start_time FROM active_voice_sessions
                    WHERE user_id = ?
                ''', (user_id,))

                session = self.cursor.fetchone()
                if not session:
                    return

                guild_id, session_channel_id, start_time = session
                start_datetime = datetime.fromisoformat(start_time)
                duration_minutes = (datetime.now() - start_datetime).total_seconds() / 60

                # Only log if session was longer than 30 seconds
                if duration_minutes > 0.5:
                    # Insert completed session
                    self.cursor.execute('''
                        INSERT INTO voice_sessions (user_id, guild_id, channel_id, start_time, end_time, duration_minutes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, guild_id, session_channel_id, start_time, datetime.now(), duration_minutes))

                    # Update daily stats
                    today = datetime.now().date()
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO daily_stats (user_id, guild_id, date, voice_minutes)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, guild_id, today, duration_minutes))

                    self.cursor.execute('''
                        UPDATE daily_stats SET voice_minutes = voice_minutes + ?
                        WHERE user_id = ? AND guild_id = ? AND date = ?
                    ''', (duration_minutes, user_id, guild_id, today))

                    # Update global XP
                    await self._update_global_xp(user_id, guild_id, 'voice', duration_minutes)

                # Remove active session
                self.cursor.execute('DELETE FROM active_voice_sessions WHERE user_id = ?', (user_id,))
                self.conn.commit()

            except Exception as e:
                logger.error(f"Error ending voice session: {e}")
                self.conn.rollback()

    async def _end_existing_voice_session(self, user_id: int):
        """Helper to end any existing voice session."""
        self.cursor.execute('SELECT channel_id FROM active_voice_sessions WHERE user_id = ?', (user_id,))
        existing = self.cursor.fetchone()
        if existing:
            await self.end_voice_session(user_id, existing[0])

    async def _update_global_xp(self, user_id: int, guild_id: int, activity_type: str, value: float = 0):
        """Update global XP and level system."""
        try:
            # Calculate XP based on activity
            xp_gain = 0
            if activity_type == 'message':
                base_xp = 1
                word_bonus = min(value * 0.1, 5)  # Max 5 bonus XP for long messages
                xp_gain = base_xp + word_bonus
            elif activity_type == 'voice':
                xp_gain = value * 0.5  # 0.5 XP per minute

            # Get current user data
            self.cursor.execute('''
                SELECT global_level, global_xp, total_messages, total_voice_minutes, total_servers, last_daily_activity, daily_streak
                FROM global_user_levels WHERE user_id = ?
            ''', (user_id,))

            user_data = self.cursor.fetchone()
            today = datetime.now().date()

            if user_data:
                current_level, current_xp, total_msg, total_voice, total_servers, last_daily, daily_streak = user_data

                # Check for daily streak
                if last_daily:
                    last_date = datetime.strptime(last_daily, '%Y-%m-%d').date()
                    if today == last_date + timedelta(days=1):
                        daily_streak += 1
                    elif today != last_date:
                        daily_streak = 1
                else:
                    daily_streak = 1

                # Update stats
                new_xp = current_xp + xp_gain
                new_level = self._calculate_level(new_xp)

                if activity_type == 'message':
                    total_msg += 1
                elif activity_type == 'voice':
                    total_voice += value

                # Count unique servers (simplified - you might want to track this differently)
                self.cursor.execute('SELECT COUNT(DISTINCT guild_id) FROM messages WHERE user_id = ?', (user_id,))
                server_count = self.cursor.fetchone()[0] or 1

                self.cursor.execute('''
                    UPDATE global_user_levels 
                    SET global_level = ?, global_xp = ?, total_messages = ?, total_voice_minutes = ?, 
                        total_servers = ?, last_activity = ?, last_daily_activity = ?, daily_streak = ?,
                        best_streak = MAX(best_streak, ?)
                    WHERE user_id = ?
                ''', (new_level, new_xp, total_msg, total_voice, server_count, datetime.now(),
                      today, daily_streak, daily_streak, user_id))

                # Check for level up achievements
                if new_level > current_level:
                    await self._check_level_achievements(user_id, new_level)

            else:
                # Create new user
                initial_level = self._calculate_level(xp_gain)
                self.cursor.execute('''
                    INSERT INTO global_user_levels 
                    (user_id, global_level, global_xp, total_messages, total_voice_minutes, total_servers, 
                     last_daily_activity, daily_streak, best_streak)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, initial_level, xp_gain, 1 if activity_type == 'message' else 0,
                      value if activity_type == 'voice' else 0, 1, today, 1, 1))

        except Exception as e:
            logger.error(f"Error updating global XP: {e}")

    def _calculate_level(self, xp: float) -> int:
        """Calculate level based on XP using a logarithmic scale."""
        if xp < 0:
            return 1
        # Level formula: level = floor(sqrt(xp/100)) + 1
        import math
        return int(math.sqrt(xp / 100)) + 1

    def _xp_for_level(self, level: int) -> int:
        """Calculate XP required for a specific level."""
        return (level - 1) ** 2 * 100

    async def get_user_stats(self, user_id: int, hours: int = 24, guild_id: Optional[int] = None) -> Tuple[int, float]:
        """Get user statistics for a time period."""
        async with self.lock:
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)

                # Message count
                if guild_id:
                    self.cursor.execute('''
                        SELECT COUNT(*) FROM messages 
                        WHERE user_id = ? AND guild_id = ? AND timestamp > ?
                    ''', (user_id, guild_id, cutoff_time))
                else:
                    self.cursor.execute('''
                        SELECT COUNT(*) FROM messages 
                        WHERE user_id = ? AND timestamp > ?
                    ''', (user_id, cutoff_time))

                message_count = self.cursor.fetchone()[0] or 0

                # Voice time
                if guild_id:
                    self.cursor.execute('''
                        SELECT COALESCE(SUM(duration_minutes), 0) FROM voice_sessions 
                        WHERE user_id = ? AND guild_id = ? AND start_time > ?
                    ''', (user_id, guild_id, cutoff_time))
                else:
                    self.cursor.execute('''
                        SELECT COALESCE(SUM(duration_minutes), 0) FROM voice_sessions 
                        WHERE user_id = ? AND start_time > ?
                    ''', (user_id, cutoff_time))

                voice_minutes = self.cursor.fetchone()[0] or 0

                return message_count, voice_minutes

            except Exception as e:
                logger.error(f"Error getting user stats: {e}")
                return 0, 0

    async def get_global_user_info(self, user_id: int) -> Optional[Dict]:
        """Get global user information including level and achievements."""
        async with self.lock:
            try:
                self.cursor.execute('''
                    SELECT global_level, global_xp, total_messages, total_voice_minutes, total_servers,
                           daily_streak, best_streak, first_seen, achievements
                    FROM global_user_levels WHERE user_id = ?
                ''', (user_id,))

                result = self.cursor.fetchone()
                if not result:
                    return None

                level, xp, total_msg, total_voice, servers, streak, best_streak, first_seen, achievements = result

                # Calculate XP for next level
                next_level_xp = self._xp_for_level(level + 1)
                current_level_xp = self._xp_for_level(level)
                xp_progress = xp - current_level_xp
                xp_needed = next_level_xp - current_level_xp

                return {
                    'level': level,
                    'xp': xp,
                    'xp_progress': xp_progress,
                    'xp_needed': xp_needed,
                    'total_messages': total_msg,
                    'total_voice_minutes': total_voice,
                    'total_servers': servers,
                    'daily_streak': streak,
                    'best_streak': best_streak,
                    'first_seen': first_seen,
                    'achievements': json.loads(achievements) if achievements else []
                }

            except Exception as e:
                logger.error(f"Error getting global user info: {e}")
                return None

    async def get_leaderboard(self, limit: int = 10, guild_id: Optional[int] = None) -> List[Tuple]:
        """Get global or guild-specific leaderboard."""
        async with self.lock:
            try:
                if guild_id:
                    # Guild-specific leaderboard based on recent activity
                    self.cursor.execute('''
                        SELECT user_id, COUNT(*) as messages, 
                               COALESCE(SUM(word_count), 0) as total_words
                        FROM messages 
                        WHERE guild_id = ? AND timestamp > datetime('now', '-30 days')
                        GROUP BY user_id
                        ORDER BY messages DESC
                        LIMIT ?
                    ''', (guild_id, limit))
                else:
                    # Global leaderboard
                    self.cursor.execute('''
                        SELECT user_id, global_level, global_xp, total_messages, total_voice_minutes
                        FROM global_user_levels
                        ORDER BY global_xp DESC
                        LIMIT ?
                    ''', (limit,))

                return self.cursor.fetchall()

            except Exception as e:
                logger.error(f"Error getting leaderboard: {e}")
                return []

    async def _check_level_achievements(self, user_id: int, new_level: int):
        """Check and award level-based achievements."""
        achievements = []

        level_milestones = {
            5: ("Newcomer", "Reached level 5!", "🌟"),
            10: ("Regular", "Reached level 10!", "⭐"),
            25: ("Veteran", "Reached level 25!", "🏅"),
            50: ("Expert", "Reached level 50!", "🏆"),
            100: ("Legend", "Reached level 100!", "👑")
        }

        for milestone, (name, desc, icon) in level_milestones.items():
            if new_level >= milestone:
                # Check if already has this achievement
                self.cursor.execute('''
                    SELECT id FROM user_achievements 
                    WHERE user_id = ? AND achievement_name = ?
                ''', (user_id, name))

                if not self.cursor.fetchone():
                    self.cursor.execute('''
                        INSERT INTO user_achievements (user_id, achievement_name, description, icon)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, name, desc, icon))
                    achievements.append((name, desc, icon))

        return achievements

    async def cleanup_old_data(self, days: int = 90):
        """Clean up old data to keep database size manageable."""
        async with self.lock:
            try:
                cutoff_date = datetime.now() - timedelta(days=days)

                # Clean old messages (keep recent ones for stats)
                self.cursor.execute('DELETE FROM messages WHERE timestamp < ?', (cutoff_date,))

                # Clean old daily stats
                self.cursor.execute('DELETE FROM daily_stats WHERE date < ?', (cutoff_date.date(),))

                # Clean old voice sessions
                self.cursor.execute('DELETE FROM voice_sessions WHERE start_time < ?', (cutoff_date,))

                self.conn.commit()
                logger.info(f"Cleaned up data older than {days} days")

            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Enhanced Stats database connection closed")