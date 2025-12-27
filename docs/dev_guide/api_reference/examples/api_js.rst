Using the API with JavaScript
=============================

This section demonstrates how to use the ManagerX API from a frontend JavaScript application.
It shows authentication handling, token refresh, and usage of various endpoints like TempVC, Welcome, Levelsystem, and Stats.

API Base
--------

All API requests are made relative to the base URL:

::

    const API_BASE = "http://127.0.0.1:3002/api";

or your Domain.

Authentication
--------------

Store and retrieve your Discord OAuth tokens from localStorage:

- Access token: `discord_token`
- Refresh token: `discord_refresh_token`

Use `checkTokenStatus()` to inspect token availability:

::

    const tokens = checkTokenStatus();
    console.log(tokens.hasToken, tokens.hasRefreshToken);

Refreshing Tokens
-----------------

Call `refreshToken()` to refresh an expired access token:

::

    await refreshToken();

API Fetch Helper
----------------

Use `apiFetch(url, options)` to make authorized requests. It automatically attaches the access token
and handles 401 errors by redirecting to the login page.

::

    const response = await apiFetch(`${API_BASE}/guild/${guildId}/tempvc`);

Example Usage
-------------

- Load guilds (servers where user has admin rights):

::

    await loadGuilds();

- Load and save TempVC settings:

::

    await loadTempVCModule(guildId);
    await saveTempVC(guildId);

- Load and save Welcome settings:

::

    await loadWelcomeModule(guildId);
    await saveWelcome(guildId);

- Load and save Levelsystem settings:

::

    await loadLevelsystemModule(guildId);
    await saveLevelsystem(guildId);

- Load bot statistics:

::

    await loadBotStats();

Notes
-----

- Always use the recommended endpoint `api/managerx/stats` for bot statistics.
- Ensure all features (TempVC, Welcome, Levelsystem) are enabled in the bot config before using them.
- API errors are logged to the console and shown via alert dialogs in this example.

