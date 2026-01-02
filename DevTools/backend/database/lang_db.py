# src/database/settings_db.py

import sqlite3
import os
from datetime import datetime

class SettingsDB:
    """
    Datenbank-Klasse zur Verwaltung von Benutzer- und Servereinstellungen.
    """
    def __init__(self, db_path="data/settings.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [DATABASE] Settings Database initialized ✓")

    def create_tables(self):
        """Erstellt die Benutzereinstellungen-Tabelle, falls sie nicht existiert."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'en'
            )
        """)
        self.conn.commit()

    def set_user_language(self, user_id: int, lang_code: str):
        """Speichert den Sprachcode für einen Benutzer."""
        self.cursor.execute("""
            INSERT OR REPLACE INTO user_settings (user_id, language)
            VALUES (?, ?)
        """, (user_id, lang_code))
        self.conn.commit()

    def get_user_language(self, user_id: int) -> str:
        """Ruft den Sprachcode für einen Benutzer ab. Standard: 'en'."""
        self.cursor.execute("SELECT language FROM user_settings WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        
        # 'en' als gewünschter Standard, falls kein Eintrag gefunden wird
        return result[0] if result else 'en'

    def close(self):
        self.conn.close()