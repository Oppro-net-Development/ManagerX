Cog System
====================
The cog system of ManagerX is designed to modularize bot functionality into separate, manageable components called cogs. Each cog encapsulates a specific set of commands and event listeners, allowing for easier maintenance, scalability, and customization of the bot's features.
Cogs are implemented as Python classes that inherit from the base Cog class provided by the Pycord library. This structure enables developers to add or remove features without affecting the core bot functionality.
Key Features of the Cog System

- **Modularity:** Each cog represents a distinct feature set, making it easy to enable or disable specific functionalities as needed.
- **Ease of Maintenance:** Isolating features into cogs simplifies debugging and updating individual components without impacting the entire bot.
- **Scalability:** New features can be added as separate cogs, allowing the bot to grow in functionality over time.
- **Event Handling:** Cogs can listen to specific events, enabling them to respond to user actions or other triggers within the Discord server.
- **Command Grouping:** Related commands can be grouped within a single cog, providing a logical organization of functionalities.
To create a new cog, developers typically define a class that extends the Cog base class and implement the desired commands and event listeners. Once defined, the cog can be loaded into the bot using the bot's load_extension method.
Overall, the cog system is a powerful architectural feature of ManagerX that enhances the bot's flexibility and maintainability, making it easier for developers to manage and expand its capabilities.

Py-cord Emample (without Ezcord)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from discord import slash_command
    from discord.ext import commands

    class MyCog(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.command()
        async def my_command(self, ctx):
            await ctx.send("This is a command from MyCog!")

    def setup(bot):
        bot.add_cog(MyCog(bot))

This example demonstrates how to define a simple cog with a command. The `setup` function is used to add the cog to the bot when it is loaded.

Ezcord Example (With Py-cord)
~~~~~~~~~~~~~~

With Ezcord, you can simplify cog creation even further:

.. code-block:: python

    import ezcord
    import discord
    from discord import slash_command

    class MyCog(ezcord.Cog):
        def __init__(self, bot):
            self.bot = bot

        @slash_command()
        async def my_command(self, ctx: discord.ApplicationContext):
            await ctx.respond("This is a command from MyCog!")

    def setup(bot: ezcord.Bot):
        bot.add_cog(MyCog(bot))

This example demonstrates how to create a cog using the Ezcord extension for Py-Cord, which extends Py-Cord's functionality by simplifying the creation of Discord bots with slash commands. Ezcord builds on top of Py-Cord, allowing developers to define slash commands more easily while maintaining compatibility with Py-Cord's core features.

Cog Loading System
------------------

Cogs are automatically loaded from the `src/cogs/` directory when the bot starts, allowing for seamless integration of new features. ManagerX uses a dynamic cog loading system that recursively scans the cogs directory and loads all Python modules.

Dynamic Cog Loading Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ManagerX bot implements dynamic cog loading through the following process:

.. code-block:: python

    def _load_all_cogs(self):
        """
        Dynamically loads all cog modules from the src/cogs/ directory.
        Returns the total number of successfully loaded cogs.
        1. Scans the cogs directory for Python files.
        2. Normalizes file paths to Python module names.
        """
        cogs_dir = "src/cogs"
        
        # Sucht rekursiv nach allen Python-Dateien in Unterordnern von cogs
        cog_files = glob.glob(f"{cogs_dir}/**/[!__]*.py", recursive=True)
        total_cogs = 0

        for file_path in cog_files:
            # 1. Normalize the path to a Python module name
            #    This ensures that the entire path is converted to Python module naming convention.
            normalized_path = file_path.replace(os.path.sep, ".").replace("/", ".")
            
            # 2. Remove the file extension '.py'
            module_name = normalized_path[:-3]
            
            # 3. CHECK: Ensure that the module name begins with 'src.cogs'
            if not module_name.startswith("src.cogs"):
                 logger.warn("COGS SKIP", f"Skipping non-standard cog path: {file_path}")
                 continue

            try:
                self.load_extension(module_name)
                logger.info(Category.COGS, f"Loaded: {module_name}")
                total_cogs += 1
            except Exception as e:
                logger.error("COGS FAIL", f"Laden von {module_name} fehlgeschlagen: {e.__class__.__name__}: {e}")
                logger.info("COGS FAIL", "--- Start Traceback ---")
                traceback.print_exc()
                logger.info("COGS FAIL", "--- Ende Traceback ---")
                
        logger.success(Category.COGS, f"Insgesamt {total_cogs} Cogs dynamisch geladen.")
        return total_cogs

How It Works
~~~~~~~~~~~~

1. **Directory Scanning**: The system uses `glob.glob()` to recursively find all Python files in the `src/cogs/` directory, excluding `__init__.py` files.

2. **Path Normalization**: File paths are converted to Python module names by:
   
   - Replacing OS-specific path separators (`\` on Windows, `/` on Unix) with dots
   - Removing the `.py` extension
   - This ensures cross-platform compatibility

3. **Module Validation**: Each found module is checked to ensure it starts with `src.cogs`, preventing loading of unintended files.

4. **Dynamic Loading**: The bot uses `self.load_extension(module_name)` to load each valid cog module, which triggers the `setup()` function defined in each cog file.

5. **Error Handling**: If a cog fails to load, the error is logged with full traceback information, but the bot continues loading other cogs.

6. **Success Reporting**: After all cogs are loaded, a success message displays the total number of cogs loaded.

Calling the Loader
~~~~~~~~~~~~~~~~~~

The cog loader is called during the bot's `on_ready()` event:

.. code-block:: python

    async def on_ready(self):
        logger.success("READY", f"Logged in as {self.user}")

        # --- COG LOADING (Short form) ---
        logger.loading(Category.COGS, "Starting dynamic cog loading...")
        self._load_all_cogs()
        # -------

This ensures all cogs are loaded after the bot successfully connects to Discord.

Directory Structure
~~~~~~~~~~~~~~~~~~~

The cogs directory structure should follow this pattern:

.. code-block::

    src/cogs/
    ├── fun/
    │   ├── __init__.py
    │   ├── jokes.py
    │   ├── weather.py
    │   └── wikipedia.py
    ├── moderation/
    │   ├── __init__.py
    │   ├── antispam.py
    │   ├── moderation.py
    │   └── warningsystem.py
    ├── informationen/
    │   ├── __init__.py
    │   ├── botstatus.py
    │   └── serverinfo.py
    └── Servermanament/
        ├── __init__.py
        ├── welcome.py
        └── logging.py

Each subdirectory should contain an `__init__.py` file (can be empty) to mark it as a Python package.

Best Practices
~~~~~~~~~~~~~~

- **Naming Convention**: Use lowercase names for cog directories and files
- **Initialization**: Always include a `setup()` function that adds the cog to the bot
- **Error Handling**: Include try-except blocks in your cogs to handle errors gracefully
- **Logging**: Use the bot's logger to report important events and errors
- **Organization**: Group related commands into the same cog based on functionality