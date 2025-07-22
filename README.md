<div align="center">
  <h1>ManagerX - Discord Bot</h1>
  <p>Ein vielseitiger Discord-Bot für Moderation, Spaß und Serververwaltung.</p>
  <img src="https://img.shields.io/badge/Version-1.3.1-blue?style=for-the-badge" alt="Version" />
  <img src="https://img.shields.io/badge/Next%20Version-V1.4-green?style=for-the-badge" alt="Next Version" />
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

### 1. 
