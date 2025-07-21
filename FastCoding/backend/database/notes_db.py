# Copyright (c) 2025 OPPRO.NET Network
import sqlite3
import os

from colorama import Fore, Style

class NotesDatabase:
    def __init__(self, base_path):
        db_path = os.path.join(base_path, "data", "notes.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                author_id INTEGER,
                author_name TEXT,
                note TEXT,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def add_note(self, guild_id, user_id, author_id, author_name, note, timestamp):
        self.cursor.execute(
            "INSERT INTO notes (guild_id, user_id, author_id, author_name, note, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, author_id, author_name, note, timestamp)
        )
        self.conn.commit()

    def get_notes(self, guild_id, user_id):
        self.cursor.execute(
            "SELECT id, note, timestamp, author_name FROM notes WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        rows = self.cursor.fetchall()
        return [
            {"id": row[0], "content": row[1], "timestamp": row[2], "author_name": row[3]}
            for row in rows
        ]

    def delete_note(self, note_id):
        self.cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_note_by_id(self, note_id):
        self.cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()
