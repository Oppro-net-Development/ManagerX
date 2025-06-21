# ManagerX — Discord Bot Projekt

![ManagerX Logo](https://github.com/Oppro-net-Development/ManagerX/blob/main/GitHub/Img/managerx.png)

Ein vielseitiger Discord-Bot mit Fokus auf **Moderation**, **Informationen**, **TempVC** und einer modularen UI-Struktur. Entwickelt mit py-cord und ezcord.

---

## 📦 Features

- 🔨 Umfangreiche Moderationsfunktionen (Verwarnungen, Admin-Tools)
- 🧾 Informationskommandos über User, Server & Bot
- 🎧 Temporäre Voicechannel-Erstellung
- 🎨 Anpassbare UI mit Emojis und Farben
- 💥 Fehler-Webhook-Integration (für Logs oder Discord-Webhooks)

---

## 📁 Projektstruktur

```
ManagerX/
├── main.py                    # Einstiegspunkt des Bots
├── .env                       # Umgebungsvariablen (z. B. TOKEN, Webhook-URLs)
├── cogs/                      # Alle Funktions-Module (Cogs)
│   ├── Fun/
│   │   ├── gewinnt.py
│   │   ├── tictactoe.py
│   │   ├── jokes.py
│   │   ├── weather.py
│   │   ├── wikipedia.py
│   ├── informationen/         # Infos über Bot, User, Server
│   │   ├── bot.py
│   │   ├── botstatus.py
│   │   ├── server.py
│   │   ├── user.py
│   ├── moderation/            # Moderation und Daten
│   │   ├── Datenbanken/
│   │   │   └── warns.db
│   │   ├── warning-system.py
│   │   ├── admin.py
│   ├── TempVC/                # Temporäre Voice Channels
│   │   └── tempvc.py
├── FastCoding/ 
│   ├── ui/                        # Benutzeroberflächen-Helfer
│       ├── colors.py              # Farbcodes für Embeds
│       ├── emojis.py              # Emoji-Konstanten
│       └── templates/
│           └── embeds.py          # Embed-Vorlagen
│   └── backend/
│       ├── config/
│       ├── database/
│           ├── __init__.py
│           ├── notes_db.py
│           ├── spam_db.py
│           ├── vc_db.py
│           ├── warn_db.py
│       ├── utils/
│           ├── __init__.py
│           ├── config.py
│           ├── utils.py
│       ├── __init__.py
│       ├── logging.py
```

---

## ⚙️ Installation

### 1. Projekt klonen
```bash
git clone https://github.com/Oppro-net-Development/ManagerX.git
cd ManagerX
```

### 2. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```
Falls requirements.txt fehlt:
```bash
pip install py-cord ezcord python-dotenv
```

### 3. .env Datei erstellen
```env
TOKEN=dein_bot_token
ERROR_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

---

## 📌 Beispiel: Cog mit UI-Elementen
```python
import ezcord
from discord.ext import commands
from ui.emojis import emoji_no

class BotInfos(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="botinfo", description="Zeigt Informationen zum Bot an")
    async def botinfo(self, ctx):
        await ctx.respond(f"{emoji_no} Hier sind die Bot-Infos!")

def setup(bot):
    bot.add_cog(BotInfos(bot))
```

---

## 🧪 Voraussetzungen

- Python 3.8+
- Discord-Bot mit aktivierten Privileged Intents
- Aktivierter Slash Command Support auf deinem Server

---

## 📌 Geplante Features / TODO

- [ ] Logging-System erweitern
- [ ] Dashboard (z. B. via Flask oder FastAPI)
- [ ] Rechteverwaltung für Slash-Befehle
- [ ] Logging-UI mit Embed-Farben je nach Severity
- [ ] Internationalisierung (z. B. EN/DE Umschaltung)

---

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

---

## 🤝 Mitwirken

Pull Requests sind willkommen!  
Fehler oder Verbesserungsvorschläge? Erstelle ein [Issue](https://github.com/Oppro-net-Development/ManagerX/issues).

---

## 📣 Entwickler

**Lenny / OPPRO.NET Development**  
[GitHub-Profil ansehen](https://github.com/Oppro-net-Development)
