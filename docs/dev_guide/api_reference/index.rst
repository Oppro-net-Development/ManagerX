API Reference
=============

Overview
--------

The API of ManagerX is built using `FastAPI <https://fastapi.tiangolo.com/>`_, a modern, fast web framework for building APIs with Python. FastAPI provides automatic interactive API documentation, type validation, and asynchronous support out of the box.

The API serves as the interface between the website, dashboard, bot, and Discord API.

API Versioning
--------------

ManagerX API currently has a single version:

- **v2**: The current and stable version. All endpoints are technically under `/api/v2/`, but it is **recommended to use `/api/managerx/stats`** for statistics-related requests. This ensures compatibility with future updates and simplifies integration.

Authentication
--------------
- OAuth2 via Discord
- `/api/auth/callback` - exchange code for access token
- `/api/auth/refresh` - refresh access token
- Admin vs user permissions explained

Error Handling
--------------
- 400 Bad Request → invalid IDs or missing parameters
- 401 Unauthorized → invalid or expired token
- 403 Forbidden → feature disabled or missing admin rights
- 500 Internal Server Error → database or Discord API issues

Notes & Best Practices
----------------------
- All responses are JSON
- Respect rate limits / cooldowns
- Only admins should call admin-only endpoints
- Store tokens securely

Contents
--------
.. toctree::
    :maxdepth: 2

    endpoints/index
    examples/index