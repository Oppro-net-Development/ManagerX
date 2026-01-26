===============================
👨‍💻 Developer Guide
===============================

**Welcome to the ManagerX Developer Guide!**

This comprehensive documentation is your resource for understanding ManagerX's architecture, extending the bot, deploying it to production, and contributing to the project. Whether you're building a new feature, self-hosting ManagerX, or simply curious about how it works, you'll find everything you need here.

.. note::
   **New to ManagerX?** Start with :doc:`getting_started/index` to set up your development environment.

.. important::
   This project is under active development. Features and APIs may change. Check back regularly for updates!

---

🚀 Quick Start Paths
====================

**Want to get up and running immediately?**

1. Install dependencies → :doc:`installation/index`
2. Understand the structure → :doc:`project_structure/index`
3. Learn the architecture → :doc:`architecture/index`
4. Start coding → :doc:`bot_development/index`

**Deploying to production?**

1. Review deployment options → :doc:`deployment/index`
2. Set up your server → :doc:`deployment/index`
3. Configure monitoring → :doc:`deployment/index`
4. Establish backups → :doc:`database/index`

**Want to contribute?**

1. Fork the repository
2. Read :doc:`contributing/index`
3. Create a feature branch
4. Follow code style → :doc:`contributing/index`
5. Write tests → :doc:`testing/index`
6. Submit a pull request!

---

📚 Documentation Structure
===========================

**Getting Started**

- :doc:`getting_started/index` — Installation, setup, first steps
- :doc:`installation/index` — Detailed installation instructions
- :doc:`project_structure/index` — Repository organization

**Understanding ManagerX**

- :doc:`architecture/index` — System design and components
- :doc:`database/index` — SQLite database schema and operations
- :doc:`bot_development/index` — Building bot features and cogs
- :doc:`api_development/index` — Creating API endpoints

**Development**

- :doc:`testing/index` — Unit tests, integration tests, testing strategy
- :doc:`deployment/index` — Production deployment, hosting options
- :doc:`contributing/index` — Contribution guidelines, PR process
- :doc:`troubleshooting/index` — Debugging and common issues

---

🏗️ Architecture Overview
=========================

ManagerX consists of three main components:

**Bot Core (Python)**

Discord.py/py-cord based bot with modular cog system. Handles Discord events, commands, and business logic.

- Location: ``src/bot/``
- Main entry: ``main.py``

**API Server (FastAPI)**

REST API providing bot data to frontend and external services.

- Location: ``src/api/``
- Port: 8040
- Runs in same process as bot

**Web Dashboard (React)**

Modern TypeScript/React frontend with real-time statistics and management interface.

- Location: ``src/web/``
- Port: 8080
- Built with Vite

See :doc:`architecture/index` for detailed architecture documentation.

---

🛠️ Development Environment
============================

**Prerequisites:**

- Python 3.11+
- Node.js 18+ (for web development)
- Git
- SQLite3 (usually included with Python)

**Quick Setup:**

.. code-block:: bash

   # Clone repository
   git clone https://github.com/ManagerX-Development/ManagerX.git
   cd ManagerX
   
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   
   # Install dependencies
   pip install -r requirements/bot_req.txt
   
   # Set up configuration
   cp config/config.yaml config/config.local.yaml
   # Edit config/config.local.yaml with your settings
   
   # Run the bot
   python main.py

For detailed setup, see :doc:`getting_started/index`.

---

📖 Common Development Tasks
============================

**Creating a New Command**

See :doc:`bot_development/index` for complete example

**Adding a Database Table**

See :doc:`database/index` for schema modifications

**Creating an API Endpoint**

See :doc:`api_development/index` for REST endpoint examples

**Writing Tests**

See :doc:`testing/index` for testing patterns

**Deploying to Production**

See :doc:`deployment/index` for deployment procedures

---

🤝 Contributing
================

We welcome contributions! Whether it's bug fixes, new features, or documentation improvements:

1. Fork the repository
2. Create a feature branch: ``git checkout -b feature/amazing-feature``
3. Follow code style (see :doc:`contributing/index`)
4. Write or update tests (see :doc:`testing/index`)
5. Commit with clear messages (see :doc:`contributing/index`)
6. Push and create a Pull Request

See :doc:`contributing/index` for complete contribution guidelines.

---

📊 Project Statistics
======================

- **Language:** Python (bot) + TypeScript (web)
- **Framework:** discord.py + FastAPI + React
- **Database:** SQLite
- **Lines of Code:** 10,000+
- **Cogs/Modules:** 10+
- **API Endpoints:** 20+
- **Commands:** 50+

---

🔗 Quick Navigation
====================

Key Sections:

.. toctree::
   :maxdepth: 1
   :caption: Getting Started
   :hidden:

   getting_started
   installation
   project_structure

.. toctree::
   :maxdepth: 1
   :caption: Core Concepts
   :hidden:

   architecture
   design_patterns
   database_design

.. toctree::
   :maxdepth: 1
   :caption: Development
   :hidden:

   bot_development
   api_development
   frontend_development
   testing

.. toctree::
   :maxdepth: 1
   :caption: Community
   :hidden:

   contributing
   code_style
   deployment

   