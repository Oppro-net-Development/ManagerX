Local Plugins (Main GitHub Repository)
=====================================

In addition to PyPI-based plugins, ManagerX also supports **local plugins** that live directly inside the **main GitHub repository**.

These plugins are intended for:
- experimental features
- optional extensions
- community contributions
- features that may become core plugins later

Local plugins are **not enabled or shipped by default**.

Design Principle
----------------

Local plugins follow the same core philosophy as external plugins:

- ❌ Not part of the default ManagerX installation
- 🔒 Do not affect the core unless explicitly enabled
- 🧪 Can evolve independently

This keeps the ManagerX core clean while still allowing flexibility and experimentation.

Repository Structure
--------------------

Local plugins are stored in a dedicated folder inside the main GitHub repository.

Example structure:

::

    plugins/
    ├── README.md
    ├── example_plugin/
    │   ├── plugin.py
    │   └── README.md
    ├── logging_plugin/
    │   ├── plugin.py
    │   └── README.md

- Each plugin lives in its own folder
- ``plugin.py`` contains the implementation
- ``README.md`` explains usage, configuration, and behavior

Local plugins **must not** modify core files directly.

Enabling Local Plugins
----------------------

Local plugins are **disabled by default**.

To enable a local plugin:
1. Place it inside the ``plugins/`` directory
2. Enable it via the ManagerX configuration
3. Restart ManagerX

Only explicitly enabled plugins are loaded.

Differences to PyPI Plugins
---------------------------

+-------------------+------------------------+-------------------------+
| Feature           | Local Plugins          | PyPI Plugins            |
+===================+========================+=========================+
| Location          | Main GitHub repository | External (PyPI)         |
+-------------------+------------------------+-------------------------+
| Installed via pip | No                     | Yes                     |
+-------------------+------------------------+-------------------------+
| Enabled by default| No                     | No                      |
+-------------------+------------------------+-------------------------+
| Naming scheme     | Flexible               | ``managerx-*`` required |
+-------------------+------------------------+-------------------------+
| Intended use      | Experimental / optional| Public distribution     |
+-------------------+------------------------+-------------------------+

Promotion to PyPI
-----------------

A local plugin can later be **promoted to a PyPI plugin** if it:
- proves stable
- has good documentation
- is useful to a wider audience

In this case, it must follow the PyPI naming scheme:

::

    managerx-[plugin-name]

Conclusion
----------

Local plugins provide a **safe space for innovation** without increasing the default footprint of ManagerX.

They allow contributors to:
- test new ideas
- share optional features
- collaborate inside the main repository

All without forcing functionality onto every ManagerX user.
Happy coding! 🚀

.. toctree::
   :maxdepth: 2
   :caption: Next Steps

    Create a PyPi Plugin <create_pypi_plugin>
    
    Plugin Guidelines <plugin_guidelines>