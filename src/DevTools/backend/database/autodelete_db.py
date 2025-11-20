import sqlite3
import json
from datetime import datetime


class AutoDeleteDB:
    def __init__(self, db_file="data/autodelete.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Erstellt alle benötigten Tabellen"""

        # Haupttabelle für AutoDelete-Konfiguration
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS autodelete (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL UNIQUE,
                duration INTEGER NOT NULL,
                exclude_pinned BOOLEAN DEFAULT 1,
                exclude_bots BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Whitelist-Tabelle
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS autodelete_whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                target_type TEXT NOT NULL CHECK (target_type IN ('role', 'user')),
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES autodelete (channel_id) ON DELETE CASCADE,
                UNIQUE (channel_id, target_id, target_type)
            )
        ''')

        # Zeitplan-Tabelle
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS autodelete_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                days TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES autodelete (channel_id) ON DELETE CASCADE
            )
        ''')

        # Statistiken-Tabelle
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS autodelete_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL UNIQUE,
                deleted_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                last_deletion TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES autodelete (channel_id) ON DELETE CASCADE
            )
        ''')

        self.conn.commit()
        self._migrate_old_data()

    def _migrate_old_data(self):
        """Migriert alte Daten zu neuer Struktur"""
        try:
            # Prüfe ob alte Spalten exist
            columns = [description[1] for description in
                       self.cursor.execute("PRAGMA table_info(autodelete)").fetchall()]

            # Füge neue Spalten hinzu falls sie nicht existieren
            if 'exclude_pinned' not in columns:
                self.cursor.execute('ALTER TABLE autodelete ADD COLUMN exclude_pinned BOOLEAN DEFAULT 1')
            if 'exclude_bots' not in columns:
                self.cursor.execute('ALTER TABLE autodelete ADD COLUMN exclude_bots BOOLEAN DEFAULT 0')
            if 'created_at' not in columns:
                self.cursor.execute('ALTER TABLE autodelete ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            if 'updated_at' not in columns:
                self.cursor.execute('ALTER TABLE autodelete ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Migration Fehler: {e}")

    # === HAUPTFUNKTIONEN ===

    def add_autodelete(self, channel_id, duration, exclude_pinned=True, exclude_bots=False):
        """Fügt oder aktualisiert AutoDelete-Konfiguration"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO autodelete 
            (channel_id, duration, exclude_pinned, exclude_bots, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (channel_id, duration, exclude_pinned, exclude_bots))

        # Erstelle Statistik-Eintrag falls nicht vorhanden
        self.cursor.execute('''
            INSERT OR IGNORE INTO autodelete_stats (channel_id)
            VALUES (?)
        ''', (channel_id,))

        self.conn.commit()

    def get_autodelete(self, channel_id):
        """Gibt nur die Dauer zurück (für Kompatibilität)"""
        self.cursor.execute("SELECT duration FROM autodelete WHERE channel_id=?", (channel_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_autodelete_full(self, channel_id):
        """Gibt vollständige Konfiguration zurück"""
        self.cursor.execute('''
            SELECT duration, exclude_pinned, exclude_bots 
            FROM autodelete WHERE channel_id=?
        ''', (channel_id,))
        return self.cursor.fetchone()

    def remove_autodelete(self, channel_id):
        """Entfernt AutoDelete-Konfiguration und alle zugehörigen Daten"""
        self.cursor.execute("DELETE FROM autodelete WHERE channel_id=?", (channel_id,))
        self.conn.commit()

    def get_all(self):
        """Gibt alle AutoDelete-Konfigurationen zurück"""
        self.cursor.execute('''
            SELECT channel_id, duration, exclude_pinned, exclude_bots 
            FROM autodelete ORDER BY channel_id
        ''')
        return self.cursor.fetchall()

    # === WHITELIST-FUNKTIONEN ===

    def add_to_whitelist(self, channel_id, target_id, target_type):
        """Fügt Eintrag zur Whitelist hinzu"""
        if target_type not in ['role', 'user']:
            raise ValueError("target_type muss 'role' oder 'user' sein")

        self.cursor.execute('''
            INSERT OR IGNORE INTO autodelete_whitelist 
            (channel_id, target_id, target_type)
            VALUES (?, ?, ?)
        ''', (channel_id, target_id, target_type))
        self.conn.commit()

    def remove_from_whitelist(self, channel_id, target_id, target_type):
        """Entfernt Eintrag aus der Whitelist"""
        self.cursor.execute('''
            DELETE FROM autodelete_whitelist 
            WHERE channel_id=? AND target_id=? AND target_type=?
        ''', (channel_id, target_id, target_type))
        self.conn.commit()

    def get_whitelist(self, channel_id):
        """Gibt Whitelist für einen Kanal zurück"""
        self.cursor.execute('''
            SELECT target_id, target_type FROM autodelete_whitelist 
            WHERE channel_id=?
        ''', (channel_id,))

        results = self.cursor.fetchall()
        whitelist = {'roles': [], 'users': []}

        for target_id, target_type in results:
            if target_type == 'role':
                whitelist['roles'].append(target_id)
            elif target_type == 'user':
                whitelist['users'].append(target_id)

        return whitelist

    def clear_whitelist(self, channel_id):
        """Löscht komplette Whitelist für einen Kanal"""
        self.cursor.execute("DELETE FROM autodelete_whitelist WHERE channel_id=?", (channel_id,))
        self.conn.commit()

    # === ZEITPLAN-FUNKTIONEN ===

    def add_schedule(self, channel_id, start_time, end_time, days):
        """Fügt Zeitplan hinzu"""
        self.cursor.execute('''
            INSERT INTO autodelete_schedules 
            (channel_id, start_time, end_time, days)
            VALUES (?, ?, ?, ?)
        ''', (channel_id, start_time, end_time, days))
        self.conn.commit()

    def remove_schedule(self, channel_id, start_time=None):
        """Entfernt Zeitplan(e)"""
        if start_time:
            self.cursor.execute('''
                DELETE FROM autodelete_schedules 
                WHERE channel_id=? AND start_time=?
            ''', (channel_id, start_time))
        else:
            self.cursor.execute('''
                DELETE FROM autodelete_schedules WHERE channel_id=?
            ''', (channel_id,))
        self.conn.commit()

    def get_schedules(self, channel_id):
        """Gibt alle Zeitpläne für einen Kanal zurück"""
        self.cursor.execute('''
            SELECT start_time, end_time, days 
            FROM autodelete_schedules 
            WHERE channel_id=?
            ORDER BY start_time
        ''', (channel_id,))
        return self.cursor.fetchall()

    # === STATISTIK-FUNKTIONEN ===

    def update_stats(self, channel_id, deleted_count=0, error_count=0):
        """Aktualisiert Statistiken"""
        timestamp = datetime.utcnow().timestamp() if deleted_count > 0 else None

        self.cursor.execute('''
            INSERT OR REPLACE INTO autodelete_stats 
            (channel_id, deleted_count, error_count, last_deletion, updated_at)
            VALUES (
                ?, 
                COALESCE((SELECT deleted_count FROM autodelete_stats WHERE channel_id=?), 0) + ?,
                COALESCE((SELECT error_count FROM autodelete_stats WHERE channel_id=?), 0) + ?,
                COALESCE(?, (SELECT last_deletion FROM autodelete_stats WHERE channel_id=?)),
                CURRENT_TIMESTAMP
            )
        ''', (channel_id, channel_id, deleted_count, channel_id, error_count, timestamp, channel_id))
        self.conn.commit()

    def get_stats(self, channel_id):
        """Gibt Statistiken für einen Kanal zurück"""
        self.cursor.execute('''
            SELECT deleted_count, error_count, last_deletion, created_at, updated_at
            FROM autodelete_stats WHERE channel_id=?
        ''', (channel_id,))

        result = self.cursor.fetchone()
        if result:
            return {
                'deleted_count': result[0],
                'error_count': result[1],
                'last_deletion': result[2],
                'created_at': result[3],
                'updated_at': result[4]
            }
        return None

    def reset_stats(self, channel_id):
        """Setzt Statistiken für einen Kanal zurück"""
        self.cursor.execute('''
            UPDATE autodelete_stats 
            SET deleted_count=0, error_count=0, last_deletion=NULL, updated_at=CURRENT_TIMESTAMP
            WHERE channel_id=?
        ''', (channel_id,))
        self.conn.commit()

    def get_global_stats(self):
        """Gibt globale Statistiken zurück"""
        self.cursor.execute('''
            SELECT 
                COUNT(*) as active_channels,
                SUM(deleted_count) as total_deleted,
                SUM(error_count) as total_errors,
                MAX(last_deletion) as latest_deletion
            FROM autodelete_stats s
            JOIN autodelete a ON s.channel_id = a.channel_id
        ''')

        result = self.cursor.fetchone()
        if result:
            return {
                'active_channels': result[0],
                'total_deleted': result[1] or 0,
                'total_errors': result[2] or 0,
                'latest_deletion': result[3]
            }
        return None

    # === EXPORT/IMPORT-FUNKTIONEN ===

    def export_all_settings(self):
        """Exportiert alle AutoDelete-Einstellungen"""
        data = {
            'exported_at': datetime.utcnow().isoformat(),
            'channels': []
        }

        # Hauptkonfigurationen
        self.cursor.execute('''
            SELECT channel_id, duration, exclude_pinned, exclude_bots, created_at, updated_at
            FROM autodelete ORDER BY channel_id
        ''')

        for row in self.cursor.fetchall():
            channel_id = row[0]
            channel_data = {
                'channel_id': channel_id,
                'duration': row[1],
                'exclude_pinned': bool(row[2]),
                'exclude_bots': bool(row[3]),
                'created_at': row[4],
                'updated_at': row[5],
                'whitelist': self.get_whitelist(channel_id),
                'schedules': self.get_schedules(channel_id),
                'stats': self.get_stats(channel_id)
            }
            data['channels'].append(channel_data)

        return data

    def import_settings(self, data, overwrite=False):
        """Importiert AutoDelete-Einstellungen"""
        imported_count = 0
        skipped_count = 0

        for channel_data in data.get('channels', []):
            channel_id = channel_data['channel_id']

            # Prüfe ob Kanal bereits existiert
            if not overwrite and self.get_autodelete(channel_id):
                skipped_count += 1
                continue

            # Importiere Hauptkonfiguration
            self.add_autodelete(
                channel_id,
                channel_data['duration'],
                channel_data.get('exclude_pinned', True),
                channel_data.get('exclude_bots', False)
            )

            # Importiere Whitelist
            if overwrite:
                self.clear_whitelist(channel_id)

            whitelist = channel_data.get('whitelist', {})
            for role_id in whitelist.get('roles', []):
                self.add_to_whitelist(channel_id, role_id, 'role')
            for user_id in whitelist.get('users', []):
                self.add_to_whitelist(channel_id, user_id, 'user')

            # Importiere Zeitpläne
            if overwrite:
                self.remove_schedule(channel_id)

            for start_time, end_time, days in channel_data.get('schedules', []):
                self.add_schedule(channel_id, start_time, end_time, days)

            imported_count += 1

        return {'imported': imported_count, 'skipped': skipped_count}

    # === WARTUNGSFUNKTIONEN ===

    def cleanup_orphaned_data(self):
        """Entfernt verwaiste Daten"""
        # Entferne Whitelist-Einträge ohne AutoDelete-Konfiguration
        self.cursor.execute('''
            DELETE FROM autodelete_whitelist 
            WHERE channel_id NOT IN (SELECT channel_id FROM autodelete)
        ''')

        # Entferne Zeitpläne ohne AutoDelete-Konfiguration
        self.cursor.execute('''
            DELETE FROM autodelete_schedules 
            WHERE channel_id NOT IN (SELECT channel_id FROM autodelete)
        ''')

        # Entferne Statistiken ohne AutoDelete-Konfiguration
        self.cursor.execute('''
            DELETE FROM autodelete_stats 
            WHERE channel_id NOT IN (SELECT channel_id FROM autodelete)
        ''')

        self.conn.commit()
        return self.cursor.rowcount

    def vacuum_database(self):
        """Optimiert die Datenbank"""
        self.cursor.execute("VACUUM")
        self.conn.commit()

    def get_database_info(self):
        """Gibt Datenbankinfos zurück"""
        info = {}

        tables = ['autodelete', 'autodelete_whitelist', 'autodelete_schedules', 'autodelete_stats']
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            info[f"{table}_count"] = self.cursor.fetchone()[0]

        # Dateigröße
        import os
        if os.path.exists(self.db_file):
            info['file_size_bytes'] = os.path.getsize(self.db_file)
            info['file_size_mb'] = round(info['file_size_bytes'] / 1024 / 1024, 2)

        return info

    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()