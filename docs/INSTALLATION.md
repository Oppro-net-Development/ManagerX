# 🚀 Installation Guide - ManagerX

Willkommen zur Installationsanleitung für ManagerX! Folge diesen Schritten, um den Bot erfolgreich einzurichten.

---

## 📋 Voraussetzungen

Bevor du mit der Installation beginnst, stelle sicher, dass folgende Komponenten installiert sind:

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **Discord Bot Token** ([Anleitung](#discord-bot-token-erstellen))

---

## ⚡ Quick Start

### 1️⃣ Repository klonen

```bash
git clone https://github.com/Oppro-net-Development/ManagerX.git
cd ManagerX
```

### 2️⃣ Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

Oder mit einem Virtual Environment (empfohlen):

```bash
# Virtual Environment erstellen
python -m venv venv

# Aktivieren (Windows)
venv\Scripts\activate

# Aktivieren (Linux/macOS)
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

### 3️⃣ Umgebungsvariablen konfigurieren

Erstelle eine `.env` Datei im Root-Verzeichnis des Projekts:

```env
# Discord Bot Token (erforderlich)
TOKEN=dein_discord_bot_token_hier
```

> ⚠️ **Wichtig:** Füge die `.env` Datei niemals zu Git hinzu! Sie sollte bereits in der `.gitignore` stehen.

> 💡 **Tipp:** Die Konfiguration des Bots erfolgt direkt über Discord-Commands nach dem Start. Weitere Einstellungen können in der Datenbank oder über Bot-Befehle vorgenommen werden.

### 4️⃣ Version überprüfen

Bevor du den Bot startest, überprüfe die Version:

**In `main.py` (Zeile 53):**
```python
BOT_VERSION = "1.7.1"
```

**Auf GitHub in `version.txt`:**
```txt
1.7.1
```

> 💡 **Tipp:** Stelle sicher, dass beide Versionen übereinstimmen, um Kompatibilitätsprobleme zu vermeiden.

### 5️⃣ Bot starten

```bash
python main.py
```

Wenn alles geklappt hat, solltest du folgende Ausgabe sehen:

```
[DEBUG] Custom language file loaded: ez_de.json
[18:50] [COGS LOADING] Loaded 19 cogs
[18:50] [BOT] Starting ManagerX...
[18:50] [STARTING UP] Logged in as ManagerX Test#5099
[UP-TO-DATE] You have the latest Version: 1.7.1
[18:50] [DATABASE] Spam database initialized successfully.
[18:50] [DATABASE] Notes database initialized successfully.
[18:50] [DATABASE] Warn database initialized successfully.
[18:50] [DATABASE] TempVC database initialized successfully.
[18:50] [DATABASE] Stats database initialized successfully.
[18:50] [DATABASE] Levelsystem database initialized successfully.
[18:50] [DATABASE] Globalchat database initialized successfully.
[18:50] [DATABASE] Logging database initialized successfully.
[18:50] [API] Weather API has Loaded.
[18:50] [DEVTOOLS] DevTools is ready to use!
```

---

## 🎯 Discord Bot Token erstellen

Falls du noch keinen Discord Bot Token hast, folge diesen Schritten:

1. **Gehe zum [Discord Developer Portal](https://discord.com/developers/applications)**
2. **Klicke auf "New Application"** und gib deinem Bot einen Namen
3. **Navigiere zu "Bot"** im linken Menü
4. **Klicke auf "Add Bot"**
5. **Kopiere den Token** unter "TOKEN" (einmal klicken auf "Reset Token" falls nötig)
6. **Aktiviere folgende Intents:**
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent

> ⚠️ **Sicherheitshinweis:** Teile deinen Token niemals mit anderen! Wenn dein Token kompromittiert wurde, setze ihn sofort im Developer Portal zurück.

---

## 🔧 Erweiterte Konfiguration

### Datenbank initialisieren

Beim ersten Start wird automatisch mehrere SQLite-Datenbank erstellt:



```bash
python main.py
```

---

## 📚 Weiterführende Dokumentation

- 📖 [Befehle & Features](COMMANDS.md)
- ⚙️ [Konfiguration](CONFIG.md)
- 🔄 [Update-Anleitung](UPDATE.md)
- 🤝 [Contributing Guide](CONTRIBUTING.md)

---

## 💬 Support

Brauchst du Hilfe? Hier sind deine Optionen:

- 💬 [Discord Support Server](https://discord.gg/tmz673WAnV)
- 🐛 [GitHub Issues](https://github.com/Oppro-net-Development/ManagerX/issues)
- 📧 [E-Mail Support](mailto:oppro.help@gmail.com)

---

<div align="center">

**🎉 Viel Erfolg mit ManagerX!**

*Made with ❤️ by OPPRO.NET*

[⬅️ Zurück zur Hauptseite](README.md)

</div>