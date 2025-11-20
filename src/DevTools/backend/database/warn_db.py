# Copyright (c) 2025 OPPRO.NET Network
import os
import sqlite3
from contextlib import contextmanager

from colorama import Fore, Style
class WarnDatabase:
    def __init__(self, base_path):
        self.db_path = os.path.join(base_path, "Datenbanken", "warns.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize the database
        self._init_database()
    def _init_database(self):
        """Initialize the database with required tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS warns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def add_warning(self, guild_id, user_id, moderator_id, reason, timestamp):
        """Add a warning to the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO warns (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (guild_id, user_id, moderator_id, reason, timestamp)
                )
                conn.commit()
                warning_id = cursor.lastrowid
                print(f"Warning added successfully with ID: {warning_id}")
                return warning_id
        except Exception as e:
            print(f"Error adding warning: {e}")
            raise

    def get_warnings(self, guild_id, user_id):
        """Get all warnings for a specific user in a guild"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, reason, timestamp FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY id DESC",
                    (guild_id, user_id)
                )
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting warnings: {e}")
            return []

    def get_warning_by_id(self, warn_id):
        """Get a specific warning by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM warns WHERE id = ?", (warn_id,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Error getting warning by ID: {e}")
            return None

    def delete_warning(self, warn_id):
        """Delete a warning by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM warns WHERE id = ?", (warn_id,))
                conn.commit()
                if cursor.rowcount > 0:
                    print(f"Warning {warn_id} deleted successfully")
                    return True
                else:
                    print(f"Warning {warn_id} not found")
                    return False
        except Exception as e:
            print(f"Error deleting warning: {e}")
            return False

    def get_warning_count(self, guild_id, user_id):
        """Get the total number of warnings for a user"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM warns WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id)
                )
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting warning count: {e}")
            return 0

    def get_total_warnings(self):
        """Get total number of warnings in database (for debugging)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM warns")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting total warnings: {e}")
            return 0