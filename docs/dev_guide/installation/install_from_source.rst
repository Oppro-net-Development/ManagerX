=============================
Install from Source Code
=============================

This guide explains how to install **ManagerX** directly from its source code. This method is ideal for developers looking to contribute or those who require the latest features from the repository.

.. note::
   If you encounter any issues during installation, please check our Troubleshooting section or open an issue on GitHub.

Prerequisites
-------------

Before proceeding, ensure you have the following installed on your system:

* **Python 3.10** or higher
* **Git**
* A valid **Discord Bot Token** from the `Discord Developer Portal <https://discord.com/developers/applications>`_

Cloning the Repository
----------------------

First, clone the ManagerX repository from GitHub and navigate into the project directory:

.. code-block:: bash

    git clone https://github.com/Oppro-net-Development/ManagerX.git
    cd ManagerX

Setting Up a Virtual Environment
--------------------------------

It is highly recommended to use a virtual environment to isolate dependencies and avoid conflicts with your system's Python packages.

**On Linux/macOS:**

.. code-block:: bash

    python3 -m venv venv
    source venv/bin/activate

**On Windows:**

.. code-block:: bash

    python -m venv venv
    .\venv\Scripts\activate

Installing Dependencies
-----------------------

ManagerX uses modular requirement files depending on your use case. Choose **one** of the following options:

**1. Standard Installation**
Basic requirements for running the application:

.. code-block:: bash

    pip install -r requirements/req.txt

**2. Bot Only**
Minimal requirements to run only the Discord bot component:

.. code-block:: bash

    pip install -r requirements/bot_req.txt

**3. Development Environment**
Includes testing frameworks and code formatters (e.g., black, pytest):

.. code-block:: bash

    pip install -r requirements/dev_req.txt

**4. Documentation Tools**
Includes tools like Sphinx for building the documentation:

.. code-block:: bash

    pip install -r requirements/docs_req.txt

Configuration
-------------

Before running the bot, you need to set up your environment variables. 

1. Create a ``.env`` file in the root directory.
2. Add your bot token as follows:

.. code-block:: text

    TOKEN=your_discord_bot_token_here

Running ManagerX
----------------

Once the installation and configuration are complete, start the application:

.. code-block:: bash

    python main.py

You should see an output indicating that **ManagerX** is successfully connected to Discord.

.. tip::
   Ensure that **Privileged Gateway Intents** (Member, Presence, Message Content) are enabled in the Discord Developer Portal under the "Bot" tab, or the bot may not function correctly.