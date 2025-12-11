Database & Database Handler 
=================================

ManagerX uses SQLite databases to persist data for various features. Each database handler is responsible for managing a specific feature's data storage.

.. toctree::
    :maxdepth: 2
    :caption: Database Handlers:
    
    AutoDelete Database <autodelete>
    Spam Detection Database <spam_detection>
    Warning System Database <warning_system>
    Welcome System Database <welcome_system>
    Level System Database <level_system>
    Logging Database <logging_system>
    Notes Database <notes_system>
    Global Chat Database <global_chat>
    Voice Channel Database <voice_channel>
    Stats Database <stats_system>


Database Overview
-----------------

The following databases are used in ManagerX:

.. list-table::
   :header-rows: 1
   :widths: 20 50 30

   * - Database File
     - Purpose
     - Handler Class
   * - `autodelete.db`
     - Auto-delete messages in channels
     - `AutoDeleteDB`
   * - `spam.db`
     - Anti-spam detection and configuration
     - `SpamDB`
   * - `warns.db`
     - User warning system
     - `WarnDatabase`
   * - `welcome.db`
     - Welcome messages and settings
     - `WelcomeDatabase`
   * - `levelsystem.db`
     - User levels and XP tracking
     - `LevelDatabase`
   * - `log_channels.db`
     - Server logging configuration
     - `LoggingDatabase`
   * - `notes.db`
     - User notes and moderator notes
     - `NotesDatabase`
   * - `globalchat.db`
     - Global chat network settings
     - `GlobalChatDB`
   * - `vc.db`
     - Voice channel management
     - `VoiceChannelDB`
   * - `stats.db`
     - Server statistics
     - `StatsDB`

Detailed Database Documentation
--------------------------------

AutoDelete Database
~~~~~~~~~~~~~~~~~~~

**File:** `data/autodelete.db`

**Purpose:** Manages auto-deletion of messages in specific channels.

**Tables:**

- **autodelete**: Main configuration table
  
  - `channel_id`: Channel ID (UNIQUE)
  - `duration`: Seconds before message deletion
  - `exclude_pinned`: Exclude pinned messages (default: 1)
  - `exclude_bots`: Exclude bot messages (default: 0)
  - `created_at`: Timestamp of creation
  - `updated_at`: Last update timestamp

- **autodelete_whitelist**: User/Role whitelist

  - `channel_id`: Reference to autodelete channel
  - `target_id`: User or Role ID
  - `target_type`: 'user' or 'role'
  - `added_at`: When added to whitelist

- **autodelete_schedules**: Scheduled deletion timeframes

  - `channel_id`: Reference to autodelete channel
  - `start_time`: Start time (HH:MM format)
  - `end_time`: End time (HH:MM format)
  - `days`: Days of week (JSON array or comma-separated)

- **autodelete_stats**: Statistics tracking

  - `channel_id`: Reference to autodelete channel
  - `deleted_count`: Total messages deleted
  - `error_count`: Failed deletion attempts
  - `last_deletion`: Timestamp of last deletion

**Key Methods:**

.. code-block:: python

    # Add or update auto-delete configuration
    add_autodelete(channel_id, duration, exclude_pinned=True, exclude_bots=False)
    
    # Add user/role to whitelist
    add_whitelist(channel_id, target_id, target_type)
    
    # Get configuration for channel
    get_autodelete(channel_id)

---

Spam Detection Database
~~~~~~~~~~~~~~~~~~~~~~~

**File:** `data/spam.db`

**Purpose:** Tracks spam patterns and manages anti-spam settings.

**Tables:**

- **spam_settings**: Server spam configuration

  - `guild_id`: Server ID (PRIMARY KEY)
  - `max_messages`: Max messages in time window
  - `time_window`: Time window in seconds
  - `action`: Action to take (kick, mute, delete)
  - `created_at`: Configuration creation date
  - `updated_at`: Last configuration update

- **spam_logs**: Spam detection logs

  - `id`: Log entry ID
  - `guild_id`: Server ID
  - `user_id`: User ID
  - `message_count`: Number of messages
  - `timestamp`: Detection timestamp
  - `action_taken`: Action that was performed

- **spam_whitelist**: Exempt users/roles

  - `guild_id`: Server ID
  - `target_id`: User or Role ID
  - `target_type`: 'user' or 'role'
  - `added_by`: User ID who added to whitelist
  - `reason`: Reason for whitelist
  - `added_at`: When added

**Features:**

- Context manager for database operations
- Automatic database migration support
- Enhanced error handling and logging
- Support for user and role whitelisting

**Key Methods:**

.. code-block:: python

    # Get spam settings for guild
    get_spam_settings(guild_id)
    
    # Update spam detection settings
    update_spam_settings(guild_id, max_messages, time_window)
    
    # Log spam detection
    add_spam_log(guild_id, user_id, message_count)
    
    # Add user to whitelist
    add_to_whitelist(guild_id, target_id, target_type, reason)

---

Warning System Database
~~~~~~~~~~~~~~~~~~~~~~~

**File:** `data/Datenbanken/warns.db`

**Purpose:** Stores user warnings for moderation.

**Tables:**

- **warns**: Warning records

  - `id`: Warning ID (PRIMARY KEY)
  - `guild_id`: Server ID
  - `user_id`: User ID
  - `moderator_id`: Moderator who issued warning
  - `reason`: Warning reason
  - `timestamp`: When warning was issued

**Key Methods:**

.. code-block:: python

    # Add warning for user
    add_warning(guild_id, user_id, moderator_id, reason, timestamp)
    
    # Get all warnings for user
    get_warnings(guild_id, user_id)
    
    # Get warning by ID
    get_warning_by_id(warn_id)
    
    # Delete warning
    delete_warning(warn_id)
    
    # Get warning count
    get_warning_count(guild_id, user_id)

---

Welcome System Database
~~~~~~~~~~~~~~~~~~~~~~~

**File:** `data/welcome.db`

**Purpose:** Manages welcome message configuration and settings.

**Tables:**

- **welcome_settings**: Server welcome configuration

  - `guild_id`: Server ID (PRIMARY KEY)
  - `channel_id`: Welcome channel ID
  - `welcome_message`: Welcome message text
  - `enabled`: Whether welcome is enabled
  - `embed_enabled`: Use embed format
  - `embed_color`: Embed color (HEX format)
  - `embed_title`: Embed title
  - `embed_description`: Embed description
  - `embed_thumbnail`: Show member avatar
  - `embed_footer`: Embed footer text
  - `ping_user`: Ping the new user
  - `delete_after`: Auto-delete after N seconds
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp

**Features:**

- Supports both text and embed messages
- Automatic database migration
- Backward compatibility with older versions
- Asynchronous and synchronous methods

**Key Methods:**

.. code-block:: python

    # Update welcome settings
    await update_welcome_settings(guild_id, channel_id=None, message=None, ...)
    
    # Get welcome settings
    await get_welcome_settings(guild_id)
    
    # Enable/disable welcome
    await toggle_welcome(guild_id, enabled)
    
    # Delete welcome settings
    await delete_welcome_settings(guild_id)

---

Level System Database
~~~~~~~~~~~~~~~~~~~~~

**File:** `data/levelsystem.db`

**Purpose:** Tracks user XP, levels, and progression.

**Tables:**

- **user_levels**: User XP and level data

  - `guild_id`: Server ID
  - `user_id`: User ID
  - `level`: Current level
  - `xp`: Current XP
  - `total_xp`: Total XP earned
  - `last_message_time`: Last message timestamp
  - `prestige_count`: Prestige level

- **level_roles**: Reward roles for levels

  - `guild_id`: Server ID
  - `level`: Level requirement
  - `role_id`: Reward role ID

- **level_settings**: Server configuration

  - `guild_id`: Server ID
  - `enabled`: Level system enabled
  - `xp_per_message`: XP per message
  - `cooldown_seconds`: Message cooldown

**Features:**

- Anti-spam detection to prevent XP farming
- Level role rewards
- Prestige system
- Caching for performance
- Comprehensive logging

**Key Methods:**

.. code-block:: python

    # Add XP to user (with anti-spam check)
    add_xp(guild_id, user_id, xp_amount)
    
    # Get user level data
    get_user_level(guild_id, user_id)
    
    # Set level role reward
    set_level_role(guild_id, level, role_id)
    
    # Get leaderboard
    get_leaderboard(guild_id, limit=10)

---

Logging Database
~~~~~~~~~~~~~~~~

**File:** `data/log_channels.db`

**Purpose:** Stores logging channel configuration for different log types.

**Tables:**

- **log_channels**: Log channel configuration

  - `guild_id`: Server ID
  - `log_type`: Type of log (member_join, member_leave, message_delete, etc.)
  - `channel_id`: Discord channel ID for logs
  - `enabled`: Whether this log type is enabled
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp

**Log Types Supported:**

- `member_join`: New member joins
- `member_leave`: Member leaves
- `member_ban`: Member banned
- `member_kick`: Member kicked
- `member_unban`: Member unbanned
- `message_delete`: Message deletion
- `message_edit`: Message editing
- `role_create`: Role created
- `role_delete`: Role deleted
- `channel_create`: Channel created
- `channel_delete`: Channel deleted

**Key Methods:**

.. code-block:: python

    # Set log channel for type
    set_log_channel(guild_id, log_type, channel_id)
    
    # Get log channel for type
    get_log_channel(guild_id, log_type)
    
    # Enable/disable log type
    set_log_enabled(guild_id, log_type, enabled)
    
    # Get all logs for guild
    get_all_logs(guild_id)

---

Notes Database
~~~~~~~~~~~~~~

**File:** `data/notes.db`

**Purpose:** Stores moderator notes about users.

**Tables:**

- **notes**: User notes

  - `id`: Note ID (PRIMARY KEY)
  - `guild_id`: Server ID
  - `user_id`: User the note is about
  - `author_id`: User who created the note
  - `author_name`: Name of note author
  - `note`: Note content
  - `timestamp`: Creation timestamp

**Key Methods:**

.. code-block:: python

    # Add note to user
    add_note(guild_id, user_id, author_id, author_name, note, timestamp)
    
    # Get all notes for user
    get_notes(guild_id, user_id)
    
    # Get specific note
    get_note_by_id(note_id)
    
    # Delete note
    delete_note(note_id)

---

Database Patterns and Best Practices
------------------------------------

Connection Management
~~~~~~~~~~~~~~~~~~~~~

All database handlers use context managers for safe connection handling:

.. code-block:: python

    @contextmanager
    def get_cursor(self):
        """Context manager for database operations"""
        cursor = self.conn.cursor()
        try:
            yield cursor
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

Error Handling
~~~~~~~~~~~~~~

Databases include comprehensive error handling:

- Custom exception classes (e.g., `SpamDBError`)
- Automatic rollback on errors
- Detailed logging of all operations
- Graceful degradation when operations fail

Caching and Performance
~~~~~~~~~~~~~~~~~~~~~~~

Some databases implement caching for frequently accessed data:

.. code-block:: python

    # Example from LevelDatabase
    self.level_roles_cache = {}
    self.enabled_guilds_cache = set()
    self.guild_configs_cache = {}

Migration Strategy
~~~~~~~~~~~~~~~~~~

Databases support automatic schema migration:

.. code-block:: python

    def _migrate_database(self):
        """Handle database migrations for schema changes"""
        # Adds new columns to existing tables
        # Migrates data from old structure to new
        # Maintains backward compatibility

Directory Structure
~~~~~~~~~~~~~~~~~~~

Database files are stored in the `data/` directory:

.. code-block::

    data/
    ├── autodelete.db
    ├── spam.db
    ├── welcome.db
    ├── levelsystem.db
    ├── log_channels.db
    ├── notes.db
    ├── globalchat.db
    ├── vc.db
    ├── stats.db
    └── Datenbanken/
        └── warns.db

Access Location
~~~~~~~~~~~~~~~

All database handlers are located in:

.. code-block::

    src/DevTools/backend/database/
    ├── __init__.py
    ├── autodelete_db.py
    ├── spam_db.py
    ├── warn_db.py
    ├── welcome_db.py
    ├── levelsystem_db.py
    ├── logging_db.py
    ├── notes_db.py
    ├── globalchat_db.py
    ├── vc_db.py
    └── stats_db.py