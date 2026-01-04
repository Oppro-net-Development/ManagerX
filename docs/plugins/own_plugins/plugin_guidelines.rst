Plugin Policy
=============

This document defines the official rules and requirements for all ManagerX
plugins, including **Local Plugins** and **PyPI Plugins**.

The goal of this policy is to keep ManagerX:
- stable
- secure
- modular
- lightweight

Plugins are never part of the core by default.

---

General Principles
------------------

- All plugins are **optional**.
- All plugins are **disabled by default**.
- The ManagerX core must never depend on plugins.
- Plugins must not modify or patch core files.

---

Plugin Types
------------

ManagerX supports two types of plugins:

1. **PyPI Plugins**  
2. **Local Plugins**  

**Local Plugins**:
- Live in the main ManagerX repository under the folder:

::

    plugins/

- Are **not Cogs**, but fully independent plugins
- Can be experimental or optional features
- Are never enabled by default

**PyPI Plugins**:
- Distributed via PyPI
- Must follow the naming convention:

::

    managerx-[plugin-name]

- Fully independent and always stored in their own GitHub repository

---

License
-------

- ManagerX itself is licensed under **GPL-3.0**.  
- Local Plugins included in the repository **must also be GPL-3.0 compatible**.  
- PyPI Plugins can use any license **compatible with GPL-3.0**.  
- Plugins without a clear license will **not be accepted**.

---

Source Code Separation Requirement
----------------------------------

All plugins, whether Local or PyPI, must have a **dedicated GitHub repository**.  

- The repository in the main ManagerX repo (`plugins/`) is only a mirror or example.  
- The **canonical source** is always the plugin's own repo.  
- One plugin = one repository.

---

Ownership & Responsibility
--------------------------

- Each plugin must have a clearly defined owner or maintainer.  
- The owner is responsible for:
  - bugs
  - security issues
  - legal matters
- ManagerX does **not** provide support for third-party plugins.

---

Security Requirements
---------------------

Plugins must not:
- contain malicious code
- collect tokens or credentials
- perform hidden network requests
- auto-update without user consent

---

Versioning Rules
----------------

- Every plugin must define a version.
- Breaking changes require a major version bump.
- Plugin versions are independent from ManagerX versions.

---

Documentation Requirement
-------------------------

Each plugin must include a `README.md` that explains:
- what the plugin does
- how to enable or install it
- configuration options
- dependencies

Plugins without documentation are not accepted.

---

Compatibility Rules
-------------------

- Plugins must declare supported ManagerX versions.
- Plugins must use only public plugin APIs.
- Plugins must not depend on private core interfaces.

---

Enable / Disable & Removal
--------------------------

- Plugins must be safely disableable.
- Plugins must not block ManagerX startup.
- Uninstalling a plugin must not leave persistent data behind.

---

Official Plugin Status
----------------------

If a plugin fulfills **all requirements** in this policy, it **may** be:

- listed in the official ManagerX documentation
- marked as an **Official ManagerX Plugin**

Official status means:
- recommended by ManagerX
- documented in the main docs
- still optional and not part of the core

Promotion is evaluated on:
- stability
- code quality
- documentation
- maintenance activity

---

Final Checklist
---------------

Before a plugin can be accepted or promoted:

- [ ] Separate GitHub repository  
- [ ] Correct naming (PyPI only)  
- [ ] License included (GPL-3.0 compatible for Local Plugins)  
- [ ] Version defined  
- [ ] README.md present  
- [ ] No core modifications  
- [ ] Disabled by default  

---

Conclusion
----------

Local and PyPI plugins provide **modularity and freedom**.  
The core remains clean and minimal, while plugins can evolve independently.  

.. toctree::
   :maxdepth: 2
   :caption: Next Steps

    Local Cog Development <create_local_plugin>
    
    Create a PyPi Plugin <create_pypi_plugin>