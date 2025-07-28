<div align="center">

# ✨ ManagerX Discord Bot ✨

*Ein vielseitiger Discord-Bot für Moderation, Spaß und Serververwaltung*

[![Version](https://img.shields.io/badge/Version-1.5-blue?style=for-the-badge&logo=github)](https://github.com/Oppro-net-Development/ManagerX)
[![Next Version](https://img.shields.io/badge/Next%20Version-V1.6-green?style=for-the-badge&logo=rocket)](https://github.com/Oppro-net-Development/ManagerX)
[![Last Commit](https://img.shields.io/github/last-commit/Oppro-net-Development/ManagerX?style=for-the-badge&logo=git)](https://github.com/Oppro-net-Development/ManagerX/commits)

[![Built with Py-Cord](https://img.shields.io/badge/Built%20with-py--cord-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://pycord.dev/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?style=for-the-badge&logo=sqlite&logoColor=003B57)](https://sqlite.org)

[![License](https://img.shields.io/github/license/Oppro-net-Development/ManagerX?style=for-the-badge)](LICENSE)
[![Issues](https://img.shields.io/github/issues/Oppro-net-Development/ManagerX?style=for-the-badge)](https://github.com/Oppro-net-Development/ManagerX/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/Oppro-net-Development/ManagerX?style=for-the-badge)](https://github.com/Oppro-net-Development/ManagerX/pulls)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-ff69b4?style=for-the-badge&logo=github)](CONTRIBUTING.md)

---

*🌟 Der ultimative Discord-Bot für deine Community - Moderation, Spaß und mehr in einem!*

[📖 Dokumentation](https://github.com/Oppro-net-Development/ManagerX/wiki) • [🐛 Bug Report](https://github.com/Oppro-net-Development/ManagerX/issues) • [💡 Feature Request](https://github.com/Oppro-net-Development/ManagerX/issues)

</div>

## 📁 Projektstruktur

```
ManagerX/
├── 🎮 cogs/                     # Bot-Module & Commands
│   ├── 🎯 fun/                 # Spaß & Entertainment
│   │   ├── gewinnt.py
│   │   ├── jokes.py
│   │   ├── tictactoe.py
│   │   ├── weather.py
│   │   └── wikipedia.py
│   ├── ℹ️ informationen/        # Information Commands
│   │   ├── botstatus.py
│   │   └── user.py
│   ├── 📈 levelsystem/         # XP & Level System
│   │   └── levelsystem.py
│   ├── 🛡️ moderation/          # Moderationstools
│   │   ├── admin.py
│   │   ├── antispam.py
│   │   ├── notes.py
│   │   └── warningsystem.py
│   ├── 🔧 servermanament/      # Server Management
│   │   ├── globalchat.py
│   │   ├── logging.py
│   │   └── stats.py
│   └── 🎤 TempVC/
│       └── tempvc.py
│
├── ⚡ FastCoding/               # Backend & UI Framework
│   ├── 🔙 backend/
│   │   ├── ⚙️ config/
│   │   │   ├── __init__.py
│   │   │   ├── links.py
│   │   │   └── permission.py
│   │   ├── 🗄️ database/
│   │   │   ├── __init__.py
│   │   │   ├── globalchat_db.py
│   │   │   ├── levelsystem_db.py
│   │   │   ├── logging_db.py
│   │   │   ├── notes_db.py
│   │   │   ├── spam_db.py
│   │   │   ├── Stats_db.py
│   │   │   ├── vc_db.py
│   │   │   └── warn_db.py
│   │   ├── 🛠️ utils/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── utils.py
│   │   ├── __init__.py
│   │   └── logging.py
│   ├── 🖼️ ui/
│   │   ├── 📄 templates/
│   │   │   └── embeds.py
│   │   ├── __init__.py
│   │   └── emojis.py
│   └── __init__.py
│
├── 🔐 .env                     # Umgebungsvariablen (Sensible Daten)
├── 🇩🇪 ez_de.json              # Deutsche Sprachdatei
├── 🇺🇸 ez_en.json              # Englische Sprachdatei
├── 📜 LICENSE                  # MIT Lizenz
├── 🚀 main.py                  # Bot Startpunkt
├── 📖 README.md                # Projekt Dokumentation
└── 📦 req.txt                  # Python Dependencies
