Fun Commands Overview
===========================
This section provides an overview of the fun commands available in ManagerX. These commands are designed to add a bit of enjoyment and entertainment to your experience while using the tool. Whether you're looking to lighten the mood during a long work session or just want to have some fun, these commands are sure to bring a smile to your face.

.. admonition:: Command

    **Command:** `/joke`

    **Description:** Tells a random joke to lighten the mood.

    **Example:**
    
    .. code-block::
    
        /joke

    The bot responds with a random joke.

    **Return Value:** A joke string.

.. admonition:: Command

    **Command:** `/connect4`

    **Description:** Starts a game of Connect 4 with another user.

    **Parameters:**
    
    - `user` (required): The user to challenge to a game of Connect 4
    
    **Example:**
    
    .. code-block::
    
        /connect4 @User

    The bot initiates a Connect 4 game with the mentioned user.

    **Return Value:** Game board and turn prompt.

.. admonition:: Command

    **Command:** `/tictactoe`

    **Description:** Starts a game of Tic Tac Toe with another user.

    **Parameters:**
    
    - `user` (required): The user to challenge to a game of Tic Tac Toe
    
    **Example:**
    
    .. code-block::
    
        /tictactoe @User

    The bot initiates a Tic Tac Toe game with the mentioned user.

    **Return Value:** Game board and turn prompt.

.. admonition:: Command

    **Command:** `/weather`
    
    **Description:** Provides the current weather information for a specified city.

    **Parameters:**
    
    - `city` (required): The name of the city to get the weather for.
    
    **Example:**
    
    .. code-block::
    
        /weather London

    The bot provides the current weather information for London.

    **Return Value:** Weather details including temperature, humidity, and conditions.

.. toctree::
   :maxdepth: 2
   :caption: Fun Commands:

   Wikipedia Commands <wikipedia>