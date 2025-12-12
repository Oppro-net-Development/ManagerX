Antispam Commands
==============================

This section of the User Guide provides detailed information about the antispam commands available in ManagerX. Each command is explained with its purpose, usage syntax, and examples to help you understand how to effectively utilize them in your projects.

AntiSpam Setup Command
=========================

.. admonition:: Command

    **Command:** `/antispam setup`
    
    **Description:** Enables the antispam system in the server.

    **Parameters:**
    
    - `log_channel` (required): The channel where spam logs will be sent.
    - `max_messages` (required): The maximum number of messages allowed within the time frame.
    - `time_frame` (required): The time frame in seconds to monitor messages.

    **Example:**
    
    .. code-block::
    
        /antispam setup #spam-logs 5 10

    Enables the antispam system with a log channel of `#spam-logs`, allowing a maximum of 5 messages within 10 seconds.
    
    **Return Value:** Confirmation of the setup or error message.

AntiSpam Set Command
=========================

.. admonition:: Command

    **Command:** `/antispam set`
    
    **Description:** Sets the antispam parameters for the server.

    **Parameters:**
    
    - `max_messages` (required): The maximum number of messages allowed within the time frame.
    - `time_frame` (required): The time frame in seconds to monitor messages.

    **Example:**
    
    .. code-block::
    
        /antispam set 3 5

    Sets the antispam parameters to allow a maximum of 3 messages within 5 seconds.
    
    **Return Value:** Confirmation of the parameter update or error message.

AntiSpam Log Channel Command
=================================

.. admonition:: Command

    **Command:** `/antispam log-channel`
    
    **Description:** Sets the log channel for antispam actions.

    **Parameters:**
    
    - `log_channel` (required): The channel where spam logs will be sent.

    **Example:**
    
    .. code-block::
    
        /antispam log-channel #new-spam-logs

    Sets the log channel to `#new-spam-logs`.
    
    **Return Value:** Confirmation of the log channel update or error message.

AntiSpam View Command
=========================

.. admonition:: Command

    **Command:** `/antispam view`
    
    **Description:** Displays the current antispam settings for the server.

    **Example:**
    
    .. code-block::
    
        /antispam view

    Displays the current antispam settings including log channel, max messages, and time frame.
    
    **Return Value:** Current antispam settings or error message.

AntiSpam Logs Command
=========================

.. admonition:: Command

    **Command:** `/antispam logs`
    
    **Description:** Displays recent antispam logs.

    **Parameters:**
    
    - `limit` (optional): The number of log entries to display (default is 10).

    **Example:**
    
    .. code-block::
    
        /antispam logs 5

    Displays the 5 most recent antispam log entries.
    
    **Return Value:** Recent antispam logs or error message.

AntiSpam Clear Command
=========================

.. admonition:: Command

    **Command:** `/antispam clear`
    
    **Description:** Clears all antispam logs.

    **Example:**
    
    .. code-block::
    
        /antispam clear

    Clears all antispam log entries.
    
    **Return Value:** Confirmation of log clearance or error message.

AntiSpam Whitelist Command
=========================

.. admonition:: Command

    **Command:** `/antispam whitelist`
    
    **Description:** Adds a member to the antispam whitelist.

    **Parameters:**
    
    - `member` (required): The member to be whitelisted.

    **Example:**
    
    .. code-block::
    
        /antispam whitelist @User

    Adds the member `@User` to the antispam whitelist.
    
    **Return Value:** Confirmation of whitelisting or error message.

AntiSpam Disable Command
=========================

.. admonition:: Command

    **Command:** `/antispam disable`
    
    **Description:** Disables the antispam system in the server.

    **Example:**
    
    .. code-block::
    
        /antispam disable

    Disables the antispam system.
    
    **Return Value:** Confirmation of disabling or error message.