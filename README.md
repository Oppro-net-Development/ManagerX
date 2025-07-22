<div align="center">
<h1> ✨ ManagerX - Discord Bot ✨ </h1>

Ein vielseitiger Discord-Bot für Moderation, Spaß und Serververwaltung.

![Version](https://img.shields.io/badge/Version-1.3.1-blue?style=for-the-badge)
![Next Version](https://img.shields.io/badge/Next%20Version-V1.4-green?style=for-the-badge)
![Last Commit](https://img.shields.io/github/last-commit/Oppro-net-Development/ManagerX?style=for-the-badge)
![Built with Py-Cord](https://img.shields.io/badge/Built%20with-py--cord-7289DA?style=for-the-badge&logo=discord&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?style=for-the-badge&logo=sqlite&logoColor=003B57)
![License](https://img.shields.io/github/license/Oppro-net-Development/ManagerX?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/Oppro-net-Development/ManagerX?style=for-the-badge)
![Pull Requests](https://img.shields.io/github/issues-pr/Oppro-net-Development/ManagerX?style=for-the-badge)
![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-ff69b4?style=for-the-badge)

</div>
---

## 📁 Dateistruktur

```plaintext
ManagerX/
│
├── cogs/                        # Alle Bot-Module
│   ├── fun/                    # Spaß-Befehle
│   │   ├── gewinnt.py
│   │   ├── jokes.py
│   │   ├── tictactoe.py
│   │   ├── weather.py
│   │   └── wikipedia.py
│   ├── informationen/          # Info-Befehle
│   │   ├── botstatus.py
│   │   └── user.py
│   ├── levelsystem/            # Level-System
│   │   └── levelsystem.py
│   ├── moderation/             # Moderationstools
│   │   ├── admin.py
│   │   ├── antispam.py
│   │   ├── notes.py
│   │   └── warningsystem.py
│   ├── servermanament/         # Servermanagement
│   │   ├── globalchat.py
│   │   ├── logging.py
│   │   └── stats.py
│   └── TempVC/
│       └── tempvc.py
│
├── FastCoding/                 # Backend & UI
│   ├── backend/
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── links.py
│   │   │   └── permission.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── globalchat_db.py
│   │   │   ├── levelsystem_db.py
│   │   │   ├── logging_db.py
│   │   │   ├── notes_db.py
│   │   │   ├── spam_db.py
│   │   │   ├── Stats_db.py
│   │   │   ├── vc_db.py
│   │   │   └── warn_db.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── utils.py
│   │   ├── __init__.py
│   │   └── logging.py
│   ├── ui/
│   │   ├── templates/
│   │   │   └── embeds.py
│   │   ├── __init__.py
│   │   └── emojis.py
│   └── __init__.py
│
├── .env                        # Umgebungsvariablen
├── ez_de.json                  # Deutsche Sprachdatei
├── ez_en.json                  # Englische Sprachdatei
├── LICENSE                     # Lizenz
├── main.py                     # Startpunkt des Bots
├── README.md                   # Diese Datei
└── req.txt                     # Abhängigkeiten
```

# 🚀 Installation
### Voraussetzungen

---

- Python 3.10 oder neuer
- Git (optional)

### 1. Repository klonen (optional)
```bash
https://github.com/Oppro-net-Development/ManagerX.git
cd ManagerX
```

### 2. Abhängigkeiten installieren
```bash
pip install -r req.txt
```

### 3. ```.env``` Datei einrichten
Erstelle eine ```.env``` Datei mit folgendem Inhalt:
```env
TOKEN=dein_discord_bot_token
ERROR_WEBHOOK_URL = https://discord.com/api/webhooks/
```

### 4. Bot starten
```bash
python main.py
```

---

# 🤝 Mitwirken
Du willst helfen? Forke das Projekt, erstelle einen Branch und sende einen Pull Request!

---

# 📜 Lizenz
Dieses Projekt steht unter der MIT-Lizenz. Weitere Infos in der Datei ```LICENSE```.
