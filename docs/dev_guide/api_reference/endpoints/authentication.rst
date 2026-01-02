Authentication API
==================

This section documents the authentication endpoints available in ManagerX. 
These endpoints handle Discord OAuth2 login and token refresh for users.

Available Endpoints
-------------------

1. **OAuth2 Callback**

   - **Endpoint**: ``/api/auth/callback``
   - **Method**: GET
   - **Description**: Exchanges the authorization code from Discord for access and refresh tokens, and returns the authenticated user's info.

   **Query Parameters**:

   - ``code`` (str, required): The authorization code provided by Discord after user login.

   **Response Example**::

       {
           "access_token": "ACCESS_TOKEN_HERE",
           "refresh_token": "REFRESH_TOKEN_HERE",
           "user": {
               "id": "123456789012345678",
               "username": "ExampleUser",
               "discriminator": "1234",
               "avatar": "avatar_hash"
           }
       }

   **Error Responses**:

   - 400 Bad Request: Discord token exchange failed.

   **Example Usage with Python requests**::

       import requests

       code = "AUTHORIZATION_CODE_FROM_DISCORD"
       response = requests.get(f"https://api.yourdomain.com/api/auth/callback?code={code}")
       data = response.json()
       print(data)

---

2. **Refresh Access Token**

   - **Endpoint**: ``/api/auth/refresh``
   - **Method**: POST
   - **Description**: Refreshes the access token using a valid refresh token.

   **Request Body (JSON)**::

       {
           "refresh_token": "REFRESH_TOKEN_HERE"
       }

   **Response Example**::

       {
           "access_token": "NEW_ACCESS_TOKEN",
           "refresh_token": "NEW_REFRESH_TOKEN"
       }

   **Error Responses**:

   - 400 Bad Request: Missing refresh token.
   - 400 Bad Request: Token refresh failed.

   **Example Usage with Python requests**::

       import requests

       data = {"refresh_token": "REFRESH_TOKEN_HERE"}
       response = requests.post("https://api.yourdomain.com/api/auth/refresh", json=data)
       tokens = response.json()
       print(tokens)

Notes
-----

- All responses are returned in **JSON format**.  
- Tokens should be stored securely by the client.  
- The `/auth/callback` endpoint requires a valid **Discord OAuth2 authorization code**.  
- The `/auth/refresh` endpoint requires a **refresh token** previously obtained from `/auth/callback`.
