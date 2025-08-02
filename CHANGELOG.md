# Changelog
### Von der letzten Version bis 1.0alpha1 

# V1.6.1
## ✏️ Geänderte Dateien

- `.gitignore` 
- `cogs/Servermanament/globalchat.py` 
- `cogs/Servermanament/logging.py` 
- `cogs/Servermanament/stats.py` 
- `cogs/Temp/tempvc.py` 
- `cogs/levelsystem/levelsystem.py` 
- `cogs/moderation/moderation.py` 

---

# V1.6
## ✏️ Geänderte Dateien
- `FastCoding/backend/database/autodelete_db.py`
- `FastCoding/backend/database/logging_db.py`
- `cogs/Servermanament/autodelete.py`
- `cogs/moderation/moderation.py`
- `main.py`

# V1.5

## 📦 Neue Dateien

- `cogs/Servermanament/autodelete.py` – Automatisches Löschen von Nachrichten  
- `FastCoding/backend/database/autodelete_db.py` – Datenbankmodul für Autodelete

---

## ✏️ Geänderte Dateien

- `FastCoding/backend/database/__init__.py`  
- `FastCoding/ui/templates/embeds.py`  
- `cogs/Servermanament/stats.py`  
- `cogs/fun/wikipedia.py`  
- `cogs/levelsystem/levelsystem.py`  
- `cogs/moderation/moderation.py`

# V1.4

## 📦 Neue Dateien

- `cogs/informationen/serverinfo.py` – Neues Cog für Serverinformationen

---

## ✏️ Geänderte Dateien

- `cogs/Servermanament/globalchat.py`  
- `cogs/Servermanament/logging.py`  
- `main.py`

---

## 🐞 Bugfixes

- Das Problem mit doppeltem Senden von Nachrichten beim Bearbeiten in `cogs/Servermanament/logging.py` wurde behoben.

# V1.3
## 📦 Neue Dateien

- `FastCoding/backend/database/logging_db.py` – Neues Datenbankmodul für Logging-Funktionen  
- `cogs/Servermanament/logging.py` – Neues Cog zur Verwaltung des Loggings

---

## ✏️ Geänderte Dateien

- `FastCoding/backend/database/__init__.py`  
- `FastCoding/backend/database/globalchat_db.py`  
- `FastCoding/backend/logging.py`  
- `cogs/informationen/botstatus.py`

# V1.2
## 📦 Neue Dateien

- `FastCoding/backend/database/levelroles_db.py` – Neues Datenbankmodul zur Speicherung und Verwaltung von Levelrollen
- `cogs/levelsystem/levelsystem.py` – Neues Cog zur Verwaltung des Levelsystems (XP, Fortschritt, Rollenvergabe)

---

## ✏️ Geänderte Dateien

- `FastCoding/backend/database/__init__.py` – Datenbankinitialisierung für neue Module erweitert
- `cogs/Servermanament/globalchat.py` – Verbesserte Globalchat-Logik und kleinere Bugfixes
- `FastCoding/backend/database/globalchat_db.py` – Optimierte Datenbankabfragen & Strukturierungen


# 1.apha0

## Was ist neu?

- 🔧 **Verbesserte Fehlerbehandlung:** Der Bot erkennt und meldet Fehler jetzt noch zuverlässiger – falls mal was schiefgeht, wissen wir direkt Bescheid!
- ⚙️ **Optimiertes Cog-Loading:** Cogs werden jetzt schneller und stabiler geladen, das spart Ladezeit beim Start.
- 🛠️ **Fixes beim Warning-System:** Kleinere Bugs bei den Verwarnungen wurden behoben, damit die Moderation noch besser klappt.
- 🎨 **UI-Verbesserungen:** Emojis und Embed-Farben wurden feingetuned für mehr Übersichtlichkeit.
- 📚 **Dokumentation erweitert:** Die README wurde aktualisiert und enthält jetzt noch mehr Infos zum Setup und zur Nutzung.