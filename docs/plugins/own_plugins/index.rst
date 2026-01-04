Developing Your Own Plugins for ManagerX
========================================

Extend ManagerX with your own custom functionality! This guide helps you create plugins, 
whether as local Cogs in the bot or as standalone PyPi projects, from setup to deployment.

Getting Started
---------------

Before you begin, make sure you have:

- Python 3.8+ installed
- A basic understanding of Python
- Familiarity with the ManagerX bot architecture

1. Set Up Your Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Install all dependencies required by ManagerX.
- Clone the ManagerX repository from GitHub to get the latest codebase.
- For PyPi plugins, ensure you have `setuptools` and `wheel` installed to package your plugin.

2. Understand the Plugin Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Local Cogs**: look inside the `cogs` or `plugins` directory. Each plugin is typically a single Python file or module.
- **PyPi Plugins**: structure your project like a standard Python package with a `setup.py` or `pyproject.toml` file.
- Review existing plugins to understand naming conventions, commands, and event listeners.

3. Create Your Plugin
~~~~~~~~~~~~~~~~~~~~

**Local Cog Example:**

.. code-block:: python

    from discord.ext import commands

    class MyPlugin(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.slash_command(name="hello", description="Say hello!")
        async def hello(self, ctx):
            await ctx.respond(f"Hello, {ctx.author.mention}!")

    def setup(bot):
        bot.add_cog(MyPlugin(bot))

**PyPi Plugin Tips:**

- Wrap your plugin in a package structure (`myplugin/`)
- Include a `setup.py` or `pyproject.toml` for distribution
- Make sure your Cog is loaded automatically when installed

4. Register Your Plugin
~~~~~~~~~~~~~~~~~~~~~~

- **Local Cogs**: add the Cog in your bot’s `setup` function or main script.
- **PyPi Plugins**: once installed via `pip`, ensure ManagerX can discover and load your plugin dynamically.

Best Practices
---------------

- Keep your plugin modular, documented, and maintainable.
- Use ManagerX’s `SimpleColoredLogs` for logging plugin events and errors.
- Follow existing naming and coding conventions for compatibility.
- For PyPi plugins, include versioning, dependencies, and metadata in your package.


.. toctree::
   :maxdepth: 2
   :caption: Next Steps

   Create a PyPi Plugin <create_pypi_plugin>
   Local Cog Development <create_local_plugin>
    Plugin Guidelines <plugin_guidelines>