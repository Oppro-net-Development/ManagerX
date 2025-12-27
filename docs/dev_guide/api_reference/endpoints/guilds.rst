Guild & Server Management API
=============================

This section documents the endpoints for managing guild-related settings in ManagerX. 
These endpoints require admin permissions on the Discord server and allow retrieving and updating server configurations such as TempVC, Welcome messages, and Levelsystem settings.

Available Endpoints
-------------------

1. **Get User Guilds**

   - **Endpoint**: ``/api/user/guilds``
   - **Method**: GET
   - **Description**: Returns the list of guilds where the user has admin permissions.
   - **Response Example**::

       [
           {
               "id": "123456789012345678",
               "name": "Example Server",
               "permissions": 8
           }
       ]

---

2. **Get Guild Channels**

   - **Endpoint**: ``/api/guild/{guild_id}/channels``
   - **Method**: GET
   - **Description**: Returns all text, voice channels and categories for the specified guild.
   - **Response Example**::

       {
           "channels": [
               {"id": "111", "name": "general", "type": 0},
               {"id": "222", "name": "voice", "type": 2}
           ]
       }

---

3. **Get TempVC Settings**

   - **Endpoint**: ``/api/guild/{guild_id}/tempvc``
   - **Method**: GET
   - **Description**: Retrieves temporary voice channel settings for the guild.
   - **Response Example**::

       {
           "creator_channel_id": "123",
           "category_id": "456",
           "auto_delete_time": 10,
           "ui_enabled": true,
           "ui_prefix": "🔧"
       }

---

4. **Save TempVC Settings**

   - **Endpoint**: ``/api/guild/{guild_id}/tempvc``
   - **Method**: POST
   - **Request Body**:

       - ``creator_channel_id`` (str)
       - ``category_id`` (str)
       - ``auto_delete_time`` (int)
       - ``ui_enabled`` (bool)
       - ``ui_prefix`` (str)
   
   - **Response Example**::

       {
           "status": "success",
           "message": "Daten wurden permanent gespeichert"
       }

---

5. **Get Welcome Settings**

   - **Endpoint**: ``/api/guild/{guild_id}/welcome``
   - **Method**: GET
   - **Description**: Retrieves the guild's welcome message settings.
   - **Response Example**::

       {
           "channel_id": "123456",
           "welcome_message": "Willkommen {user} auf {server}!",
           "enabled": true,
           "embed_enabled": false,
           "embed_color": "#00ff00",
           "embed_title": "Willkommen!",
           "embed_description": "",
           "embed_thumbnail": false,
           "embed_footer": "",
           "ping_user": false,
           "delete_after": 0
       }

---

6. **Save Welcome Settings**

   - **Endpoint**: ``/api/guild/{guild_id}/welcome``
   - **Method**: POST
   - **Request Body**: All fields as in the GET response.
   - **Response Example**::

       {
           "status": "success",
           "message": "Welcome-Einstellungen gespeichert"
       }

---

7. **Get Levelsystem Settings**

   - **Endpoint**: ``/api/guild/{guild_id}/levelsystem``
   - **Method**: GET
   - **Description**: Retrieves leveling system settings for the guild.
   - **Response Example**::

       {
           "levelsystem_enabled": true,
           "min_xp": 10,
           "max_xp": 20,
           "xp_cooldown": 30,
           "level_up_channel": "123",
           "prestige_enabled": true,
           "prestige_min_level": 50
       }

---

8. **Save Levelsystem Settings**

   - **Endpoint**: ``/api/guild/{guild_id}/levelsystem``
   - **Method**: POST
   - **Request Body**: All fields as in the GET response.
   - **Response Example**::

       {
           "status": "success",
           "message": "Levelsystem-Einstellungen gespeichert"
       }

Notes
-----

- All endpoints require a valid Discord admin token.
- Responses are returned in JSON format.
- Features must be enabled in the bot configuration; otherwise, a 403 error is returned.
- Invalid IDs or missing database entries may return 400 or 500 errors.
