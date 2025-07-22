<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=500&pause=1000&color=F75590&center=true&vCenter=true&width=435&lines=Willkommen+bei+ManagerX!;Ein+kostenloser+Discord+Bot!;Moderation%2C+Fun%2C+Logging+und+mehr!" alt="ManagerX animierte Überschrift">
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Discord-Bot-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord Bot"></a>
  <a href="#"><img src="https://img.shields.io/badge/status-Aktiv-brightgreen?style=flat&logo=serverfault" alt="Status"></a>
  <a href="#"><img src="https://img.shields.io/github/contributors/Oppro-net-Development/ManagerX?style=flat" alt="Contributors"></a>
  <a href="#"><img src="https://img.shields.io/github/last-commit/Oppro-net-Development/ManagerX?style=flat" alt="Letzter Commit"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python" alt="Python Version"></a>
  <a href="https://github.com/Oppro-net-Development/ManagerX/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Oppro-net-Development/ManagerX?style=flat-square" alt="Lizenz"></a>
  <a href="https://github.com/Oppro-net-Development/ManagerX/stargazers"><img src="https://img.shields.io/github/stars/Oppro-net-Development/ManagerX?style=flat-square" alt="GitHub Stars"></a>
</p>
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

