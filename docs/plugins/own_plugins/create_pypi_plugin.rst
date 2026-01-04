Create your own PyPI Plugin for ManagerX
=======================================

ManagerX provides a flexible **plugin system** that allows developers to extend its functionality without modifying the core project. Plugins are developed as **separate Python packages** and distributed via **PyPI**.

Plugin Philosophy
-----------------

Plugins are **not included by default** in ManagerX.

This is an intentional design decision to keep ManagerX:
- lightweight
- secure
- easy to maintain

Every plugin is installed **explicitly by the user** and lives outside the core project.

Plugin Naming Convention
------------------------

All ManagerX plugins **must** follow this naming scheme:

::

    managerx-[your-plugin-name]

Examples:
- ``managerx-logger``
- ``managerx-moderation``
- ``managerx-backup``

This naming convention ensures:
- clear identification on PyPI
- no name collisions
- automatic recognition by ManagerX

Plugin Examples on GitHub
-------------------------

The official ManagerX GitHub repository contains an **examples folder** to help developers get started.

Structure:

::

    examples/
    └── plugins/
        ├── basic_plugin/
        │   ├── plugin.py
        │   └── README.md
        ├── advanced_plugin/
        │   ├── plugin.py
        │   └── README.md

- ``.py`` files show how to implement plugins
- ``.md`` files explain the plugin logic and structure
- examples are **reference implementations**, not production code

How Plugins Work
----------------

A ManagerX plugin is a **standalone Python package** that:

- is installed via ``pip``
- exposes a defined entry point
- is detected and loaded automatically by ManagerX

Once installed, ManagerX scans for compatible plugins and enables them at runtime.

Installing a Plugin
-------------------

Plugins are installed like any other PyPI package:

::

    pip install managerx-your-plugin-name

After installation, restart ManagerX to activate the plugin.

Creating Your Own Plugin
------------------------

1. Create a new Python project
2. Name it using the required prefix: ``managerx-``
3. Implement the plugin interface
4. Add documentation (README.md)
5. Publish the package to PyPI

By following standard Python packaging rules, plugins remain:
- easy to install
- easy to update
- easy to remove

Conclusion
----------

The ManagerX plugin system is designed for **modularity and freedom**.  
You decide which features you need, and plugins provide them — without bloating the core.

Build small, focused plugins and share them with the community 🚀
Happy coding!

.. toctree::
   :maxdepth: 2
   :caption: Next Steps

    Local Cog Development <create_local_plugin>
    Plugin Guidelines <plugin_guidelines>