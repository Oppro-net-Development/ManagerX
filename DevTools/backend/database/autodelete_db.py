import sqlite3
import json
from datetime import datetime


class AutoDeleteDB:
    """
    Database manager for AutoDelete functionality in Discord channels.
    
    Manages AutoDelete configurations, whitelists, schedules, and statistics
    for automatic message deletion in Discord channels.
    
    Parameters
    ----------
    db_file : str, optional
        Path to the SQLite database file (default: "data/autodelete.db")
    
    Attributes
    ----------
    db_file : str
        Path to the database file
    conn : sqlite3.Connection
        Active database connection
    cursor : sqlite3.Cursor
        Database cursor for operations
    
    Examples
    --------
    >>> db = AutoDeleteDB("my_database.db")
    >>> db.add_autodelete(channel_id=123456, duration=3600)
    >>> db.close()
    
    Or using context manager:
    >>> with AutoDeleteDB() as db:
    ...     db.add_autodelete(channel_id=123456, duration=3600)
    """
    
    def __init__(self, db_file="data/autodelete.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """
        Create all required database tables.
        
        Creates the following tables if they don't exist:
        - autodelete: Main configuration
        - autodelete_whitelist: Whitelist for roles/users
        - autodelete_schedules: Time schedules
        - autodelete_stats: Statistics
        
        Notes
        -----
        This method is automatically called during initialization.
        """
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
        """
        Migrate old data to new structure.
        
        Adds missing columns to existing autodelete table if they don't exist.
        This ensures backward compatibility with older database versions.
        
        Notes
        -----
        Errors during migration are printed to console but don't halt execution.
        """
        try:
            columns = [description[1] for description in
                       self.cursor.execute("PRAGMA table_info(autodelete)").fetchall()]

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
            print(f"Migration error: {e}")

    # === MAIN FUNCTIONS ===

    def add_autodelete(self, channel_id, duration, exclude_pinned=True, exclude_bots=False):
        """
        Add or update AutoDelete configuration for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        duration : int
            Time in seconds before messages are deleted
        exclude_pinned : bool, optional
            Whether to exclude pinned messages from deletion (default: True)
        exclude_bots : bool, optional
            Whether to exclude bot messages from deletion (default: False)
        
        Notes
        -----
        If a configuration for the channel already exists, it will be updated.
        Automatically creates a statistics entry if one doesn't exist.
        
        Examples
        --------
        >>> db.add_autodelete(channel_id=123456, duration=3600)
        >>> db.add_autodelete(channel_id=789012, duration=7200, exclude_bots=True)
        """
        self.cursor.execute('''
            INSERT OR REPLACE INTO autodelete 
            (channel_id, duration, exclude_pinned, exclude_bots, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (channel_id, duration, exclude_pinned, exclude_bots))

        self.cursor.execute('''
            INSERT OR IGNORE INTO autodelete_stats (channel_id)
            VALUES (?)
        ''', (channel_id,))

        self.conn.commit()

    def get_autodelete(self, channel_id):
        """
        Get AutoDelete duration for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        
        Returns
        -------
        int or None
            Duration in seconds, or None if no configuration exists
        
        Notes
        -----
        This method is for backward compatibility. Use `get_autodelete_full()`
        for complete configuration details.
        
        Examples
        --------
        >>> duration = db.get_autodelete(123456)
        >>> if duration:
        ...     print(f"Messages deleted after {duration} seconds")
        """
        self.cursor.execute("SELECT duration FROM autodelete WHERE channel_id=?", (channel_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_autodelete_full(self, channel_id):
        """
        Get complete AutoDelete configuration for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        
        Returns
        -------
        tuple or None
            Tuple of (duration, exclude_pinned, exclude_bots) or None if not found
        
        Examples
        --------
        >>> config = db.get_autodelete_full(123456)
        >>> if config:
        ...     duration, exclude_pinned, exclude_bots = config
        ...     print(f"Duration: {duration}s, Exclude pinned: {exclude_pinned}")
        """
        self.cursor.execute('''
            SELECT duration, exclude_pinned, exclude_bots 
            FROM autodelete WHERE channel_id=?
        ''', (channel_id,))
        return self.cursor.fetchone()

    def remove_autodelete(self, channel_id):
        """
        Remove AutoDelete configuration and all associated data.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        
        Notes
        -----
        This cascades to delete all associated whitelist entries, schedules,
        and statistics for the channel due to foreign key constraints.
        
        Examples
        --------
        >>> db.remove_autodelete(123456)
        """
        self.cursor.execute("DELETE FROM autodelete WHERE channel_id=?", (channel_id,))
        self.conn.commit()

    def get_all(self):
        """
        Get all AutoDelete configurations.
        
        Returns
        -------
        list of tuple
            List of tuples containing (channel_id, duration, exclude_pinned, exclude_bots)
            sorted by channel_id
        
        Examples
        --------
        >>> configs = db.get_all()
        >>> for channel_id, duration, exclude_pinned, exclude_bots in configs:
        ...     print(f"Channel {channel_id}: {duration}s")
        """
        self.cursor.execute('''
            SELECT channel_id, duration, exclude_pinned, exclude_bots 
            FROM autodelete ORDER BY channel_id
        ''')
        return self.cursor.fetchall()

    # === WHITELIST FUNCTIONS ===

    def add_to_whitelist(self, channel_id, target_id, target_type):
        """
        Add an entry to the whitelist.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        target_id : int
            Discord role ID or user ID
        target_type : {'role', 'user'}
            Type of the whitelist target
        
        Raises
        ------
        ValueError
            If target_type is not 'role' or 'user'
        
        Notes
        -----
        Whitelisted roles/users will not have their messages auto-deleted.
        Duplicate entries are silently ignored.
        
        Examples
        --------
        >>> db.add_to_whitelist(channel_id=123456, target_id=789012, target_type='role')
        >>> db.add_to_whitelist(channel_id=123456, target_id=345678, target_type='user')
        """
        if target_type not in ['role', 'user']:
            raise ValueError("target_type must be 'role' or 'user'")

        self.cursor.execute('''
            INSERT OR IGNORE INTO autodelete_whitelist 
            (channel_id, target_id, target_type)
            VALUES (?, ?, ?)
        ''', (channel_id, target_id, target_type))
        self.conn.commit()

    def remove_from_whitelist(self, channel_id, target_id, target_type):
        """
        Remove an entry from the whitelist.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        target_id : int
            Discord role ID or user ID
        target_type : {'role', 'user'}
            Type of the whitelist target
        
        Examples
        --------
        >>> db.remove_from_whitelist(channel_id=123456, target_id=789012, target_type='role')
        """
        self.cursor.execute('''
            DELETE FROM autodelete_whitelist 
            WHERE channel_id=? AND target_id=? AND target_type=?
        ''', (channel_id, target_id, target_type))
        self.conn.commit()

    def get_whitelist(self, channel_id):
        """
        Get whitelist for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        
        Returns
        -------
        dict
            Dictionary with 'roles' and 'users' keys, each containing a list of IDs
        
        Examples
        --------
        >>> whitelist = db.get_whitelist(123456)
        >>> print(f"Whitelisted roles: {whitelist['roles']}")
        >>> print(f"Whitelisted users: {whitelist['users']}")
        """
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
        """
        Clear complete whitelist for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        
        Examples
        --------
        >>> db.clear_whitelist(123456)
        """
        self.cursor.execute("DELETE FROM autodelete_whitelist WHERE channel_id=?", (channel_id,))
        self.conn.commit()

    # === SCHEDULE FUNCTIONS ===

    def add_schedule(self, channel_id, start_time, end_time, days):
        """
        Add a time schedule for AutoDelete.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        start_time : str
            Start time in HH:MM format
        end_time : str
            End time in HH:MM format
        days : str
            Days when schedule is active (e.g., "Mon,Tue,Wed")
        
        Notes
        -----
        Schedules allow AutoDelete to only run during specific time windows.
        
        Examples
        --------
        >>> db.add_schedule(channel_id=123456, start_time="09:00", 
        ...                 end_time="17:00", days="Mon,Tue,Wed,Thu,Fri")
        """
        self.cursor.execute('''
            INSERT INTO autodelete_schedules 
            (channel_id, start_time, end_time, days)
            VALUES (?, ?, ?, ?)
        ''', (channel_id, start_time, end_time, days))
        self.conn.commit()

    def remove_schedule(self, channel_id, start_time=None):
        """
        Remove schedule(s) for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        start_time : str, optional
            Specific start time to remove. If None, removes all schedules
        
        Examples
        --------
        >>> db.remove_schedule(channel_id=123456, start_time="09:00")
        >>> db.remove_schedule(channel_id=123456)  # Remove all schedules
        """
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
        """
        Get all schedules for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        
        Returns
        -------
        list of tuple
            List of tuples containing (start_time, end_time, days) sorted by start_time
        
        Examples
        --------
        >>> schedules = db.get_schedules(123456)
        >>> for start, end, days in schedules:
        ...     print(f"{start}-{end} on {days}")
        """
        self.cursor.execute('''
            SELECT start_time, end_time, days 
            FROM autodelete_schedules 
            WHERE channel_id=?
            ORDER BY start_time
        ''', (channel_id,))
        return self.cursor.fetchall()

    # === STATISTICS FUNCTIONS ===

    def update_stats(self, channel_id, deleted_count=0, error_count=0):
        """
        Update statistics for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        deleted_count : int, optional
            Number of messages deleted (default: 0)
        error_count : int, optional
            Number of errors encountered (default: 0)
        
        Notes
        -----
        Counts are cumulative. The last_deletion timestamp is only updated
        if deleted_count > 0.
        
        Examples
        --------
        >>> db.update_stats(channel_id=123456, deleted_count=10)
        >>> db.update_stats(channel_id=123456, error_count=1)
        """
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
        """
        Get statistics for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        
        Returns
        -------
        dict or None
            Dictionary containing statistics or None if not found.
            Keys: 'deleted_count', 'error_count', 'last_deletion', 
                  'created_at', 'updated_at'
        
        Examples
        --------
        >>> stats = db.get_stats(123456)
        >>> if stats:
        ...     print(f"Deleted: {stats['deleted_count']} messages")
        ...     print(f"Errors: {stats['error_count']}")
        """
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
        """
        Reset statistics for a channel.
        
        Parameters
        ----------
        channel_id : int
            Discord channel ID
        
        Notes
        -----
        Sets deleted_count and error_count to 0, clears last_deletion timestamp.
        
        Examples
        --------
        >>> db.reset_stats(123456)
        """
        self.cursor.execute('''
            UPDATE autodelete_stats 
            SET deleted_count=0, error_count=0, last_deletion=NULL, updated_at=CURRENT_TIMESTAMP
            WHERE channel_id=?
        ''', (channel_id,))
        self.conn.commit()

    def get_global_stats(self):
        """
        Get global statistics across all channels.
        
        Returns
        -------
        dict or None
            Dictionary containing global statistics or None if no data exists.
            Keys: 'active_channels', 'total_deleted', 'total_errors', 'latest_deletion'
        
        Examples
        --------
        >>> stats = db.get_global_stats()
        >>> if stats:
        ...     print(f"Active channels: {stats['active_channels']}")
        ...     print(f"Total deleted: {stats['total_deleted']}")
        """
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

    # === EXPORT/IMPORT FUNCTIONS ===

    def export_all_settings(self):
        """
        Export all AutoDelete settings.
        
        Returns
        -------
        dict
            Dictionary containing all configurations, whitelists, schedules, and stats
        
        Notes
        -----
        The returned dictionary can be serialized to JSON and later imported
        using `import_settings()`.
        
        Examples
        --------
        >>> data = db.export_all_settings()
        >>> import json
        >>> with open('backup.json', 'w') as f:
        ...     json.dump(data, f, indent=2)
        """
        data = {
            'exported_at': datetime.utcnow().isoformat(),
            'channels': []
        }

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
        """
        Import AutoDelete settings.
        
        Parameters
        ----------
        data : dict
            Dictionary containing exported settings (from `export_all_settings()`)
        overwrite : bool, optional
            Whether to overwrite existing configurations (default: False)
        
        Returns
        -------
        dict
            Dictionary with 'imported' and 'skipped' counts
        
        Notes
        -----
        If overwrite is False, existing channel configurations are skipped.
        If overwrite is True, existing configurations are replaced.
        
        Examples
        --------
        >>> import json
        >>> with open('backup.json', 'r') as f:
        ...     data = json.load(f)
        >>> result = db.import_settings(data, overwrite=True)
        >>> print(f"Imported: {result['imported']}, Skipped: {result['skipped']}")
        """
        imported_count = 0
        skipped_count = 0

        for channel_data in data.get('channels', []):
            channel_id = channel_data['channel_id']

            if not overwrite and self.get_autodelete(channel_id):
                skipped_count += 1
                continue

            self.add_autodelete(
                channel_id,
                channel_data['duration'],
                channel_data.get('exclude_pinned', True),
                channel_data.get('exclude_bots', False)
            )

            if overwrite:
                self.clear_whitelist(channel_id)

            whitelist = channel_data.get('whitelist', {})
            for role_id in whitelist.get('roles', []):
                self.add_to_whitelist(channel_id, role_id, 'role')
            for user_id in whitelist.get('users', []):
                self.add_to_whitelist(channel_id, user_id, 'user')

            if overwrite:
                self.remove_schedule(channel_id)

            for start_time, end_time, days in channel_data.get('schedules', []):
                self.add_schedule(channel_id, start_time, end_time, days)

            imported_count += 1

        return {'imported': imported_count, 'skipped': skipped_count}

    # === MAINTENANCE FUNCTIONS ===

    def cleanup_orphaned_data(self):
        """
        Remove orphaned data from auxiliary tables.
        
        Returns
        -------
        int
            Number of orphaned records removed
        
        Notes
        -----
        Removes whitelist entries, schedules, and statistics that reference
        non-existent AutoDelete configurations.
        
        Examples
        --------
        >>> removed = db.cleanup_orphaned_data()
        >>> print(f"Removed {removed} orphaned records")
        """
        self.cursor.execute('''
            DELETE FROM autodelete_whitelist 
            WHERE channel_id NOT IN (SELECT channel_id FROM autodelete)
        ''')

        self.cursor.execute('''
            DELETE FROM autodelete_schedules 
            WHERE channel_id NOT IN (SELECT channel_id FROM autodelete)
        ''')

        self.cursor.execute('''
            DELETE FROM autodelete_stats 
            WHERE channel_id NOT IN (SELECT channel_id FROM autodelete)
        ''')

        self.conn.commit()
        return self.cursor.rowcount

    def vacuum_database(self):
        """
        Optimize the database.
        
        Notes
        -----
        Rebuilds the database file, repacking it into a minimal amount of disk space.
        This can improve performance but may take time on large databases.
        
        Examples
        --------
        >>> db.vacuum_database()
        """
        self.cursor.execute("VACUUM")
        self.conn.commit()

    def get_database_info(self):
        """
        Get database information and statistics.
        
        Returns
        -------
        dict
            Dictionary containing record counts for each table and file size information
        
        Examples
        --------
        >>> info = db.get_database_info()
        >>> print(f"Database size: {info['file_size_mb']} MB")
        >>> print(f"AutoDelete configs: {info['autodelete_count']}")
        """
        info = {}

        tables = ['autodelete', 'autodelete_whitelist', 'autodelete_schedules', 'autodelete_stats']
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            info[f"{table}_count"] = self.cursor.fetchone()[0]

        import os
        if os.path.exists(self.db_file):
            info['file_size_bytes'] = os.path.getsize(self.db_file)
            info['file_size_mb'] = round(info['file_size_bytes'] / 1024 / 1024, 2)

        return info

    def close(self):
        """
        Close the database connection.
        
        Notes
        -----
        Should be called when done using the database to free resources.
        Not needed when using the context manager syntax.
        
        Examples
        --------
        >>> db = AutoDeleteDB()
        >>> # ... use database ...
        >>> db.close()
        """
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()