Stats API Endpoint
==================

This section documents the statistics API endpoints available in ManagerX. 
These endpoints provide information about the bot's server count, user count, latency, and status.

Available Endpoints
-------------------

- **Version 1 API**::

    /api/managerx/stats

- **Version 2 API**::

    /api/v2/stats

HTTP Method
-----------

- **GET**: Retrieve current statistics.

Response Format
---------------

The endpoints return a JSON object with the following structure::

    {
        "stats": {
            "server_count": 50,
            "user_count": 15000
        },
        "bot_info": {
            "latency": 35,
            "status": "Online"
        }
    }

Fields
------

**stats**

- ``server_count``: Total number of servers the bot is in.
- ``user_count``: Total number of users across all servers.

**bot_info**

- ``latency``: Current bot latency in milliseconds.
- ``status``: Current status of the bot (e.g., "Online", "Offline").

Example Usage
-------------

Using **curl**::

    curl -X GET https://api.yourdomain.com/api/v2/stats

Using **Python requests**::

    import requests

    url = "https://api.yourdomain.com/api/v2/stats"
    response = requests.get(url)
    data = response.json()
    print(data)

Notes
-----

- If the local `bot_stats.json` file exists, the endpoint will return the stored stats.  
- If the file does not exist or is unreadable, default statistics will be returned.  
- All responses are in JSON format.  
- The endpoint is **read-only** and does not require authentication.
