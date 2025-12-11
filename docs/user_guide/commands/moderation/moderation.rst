Moderation Commands
=============================
This section of the User Guide provides detailed information about the moderation commands available in ManagerX. Each command is explained with its purpose, usage syntax, and examples to help you understand how to effectively utilize them in your projects.
Ban Command
=========================
.. admonition:: Command

    **Command:** `/ban`
    
    **Description:** Bans a member from the server.

    **Parameters:**
    
    - `member` (required): The member to be banned.
    - `reason` (optional): The reason for the ban.
    - `notify_user` (optional): Whether to notify the member about the ban.

    **Example:**
    
    .. code-block::
    
        /ban @User Spamming true

    Bans the member `@User` with the reason "Spamming" and notifies them about the ban.

    **Return Value:** Confirmation of the ban or error message.
Kick Command
=========================
.. admonition:: Command

    **Command:** `/kick`
    
    **Description:** Kicks a member from the server.

    **Parameters:**
    
    - `member` (required): The member to be kicked.
    - `reason` (optional): The reason for the kick.
    - `notify_user` (optional): Whether to notify the member about the kick.

    **Example:**
    
    .. code-block::
    
        /kick @User Inappropriate behavior true

    Kicks the member `@User` with the reason "Inappropriate behavior" and notifies them about the kick.

    **Return Value:** Confirmation of the kick or error message.
Timeout Commands
=========================
.. admonition:: Command

    **Command:** `/timeout`
    
    **Description:** Puts a member in timeout mode.

    **Parameters:**
    
    - `member` (required): The member to be timed out.
    - `duration` (required): The duration of the timeout (e.g., 10m, 1h, 1d).
    - `reason` (optional): The reason for the timeout.
    - `notify_user` (optional): Whether to notify the member about the timeout.

    **Example:**
    
    .. code-block::
    
        /timeout @User 10m Spamming true

    Puts the member `@User` in timeout mode for 10 minutes with the reason "Spamming" and notifies them about it.

    **Return Value:** Confirmation of the timeout or error message.
Untimeout Command
.. admonition:: Command

    **Command:** `/untimeout`
    
    **Description:** Removes timeout mode for a member.

    **Parameters:**
    
    - `member` (required): The member whose timeout should be removed.
    - `reason` (optional): The reason for removing the timeout.
    - `notify_user` (optional): Whether to notify the member about the removal of the timeout.

    **Example:**
    
    .. code-block::
    
        /untimeout @User Apology true

    Removes timeout mode for the member `@User` with the reason "Apology" and notifies them about it.

    **Return Value:** Confirmation of the timeout removal or error message.
Slowmode Command
=========================
.. admonition:: Command

    **Command:** `/slowmode`
    
    **Description:** Activates slow mode in a channel.

    **Parameters:**
    
    - `duration` (required): The duration of slow mode (e.g., 10s, 1m, 5m).
    - `reason` (optional): The reason for activating slow mode.

    **Example:**
    
    .. code-block::
    
        /slowmode 10s High message volume

    Activates slow mode for 10 seconds in the current channel with the reason "High message volume".

    **Return Value:** Confirmation of the slow mode activation or error message.
Votekick Command
=========================
.. admonition:: Command

    **Command:** `/votekick`
    
    **Description:** Starts a vote to kick a member from the server.

    **Parameters:**
    
    - `member` (required): The member to be voted for.
    - `duration` (required): The duration of the vote (e.g., 1m, 5m, 10m).
    - `reason` (optional): The reason for the vote.

    **Example:**
    
    .. code-block::
    
        /votekick @User 5m Inappropriate behavior

    Starts a vote to kick the member `@User` for 5 minutes with the reason "Inappropriate behavior".

    **Return Value:** Confirmation of the vote start or error message.



