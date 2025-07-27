import sqlite3

class AutoDeleteDB:
    def __init__(self, db_file="data/autodelete.db"):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS autodelete (
                                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                                  channel_id INTEGER NOT NULL,
                                  duration INTEGER NOT NULL)''')
        self.conn.commit()

    def add_autodelete(self, channel_id, duration):
        self.cursor.execute("INSERT OR REPLACE INTO autodelete (channel_id, duration) VALUES (?, ?)", (channel_id, duration))
        self.conn.commit()

    def get_autodelete(self, channel_id):
        self.cursor.execute("SELECT duration FROM autodelete WHERE channel_id=?", (channel_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def delete_autodelete(self, channel_id):
        self.cursor.execute("DELETE FROM autodelete WHERE channel_id=?", (channel_id,))
        self.conn.commit()

    def get_all(self):
        self.cursor.execute("SELECT channel_id, duration FROM autodelete")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
