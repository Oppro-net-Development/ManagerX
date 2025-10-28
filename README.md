<div align="center">

# 🤖 ManagerX Discord Bot

### *Der ultimative All-in-One Discord Bot für deine Community*

[![Version](https://img.shields.io/badge/Version-1.7.1-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://github.com/Oppro-net-Development/ManagerX)
[![Next Release](https://img.shields.io/badge/Next_Release-v1.7.2-00D9FF?style=for-the-badge&logo=rocket&logoColor=white)](https://github.com/Oppro-net-Development/ManagerX)
[![Last Commit](https://img.shields.io/github/last-commit/Oppro-net-Development/ManagerX?style=for-the-badge&logo=git&logoColor=white&color=F05032)](https://github.com/Oppro-net-Development/ManagerX/commits)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)

---

**Moderation • Engagement • Entertainment • Community Management**

*Entwickelt von OPPRO.NET Development | © OPPRO.NET Network*

[📥 Installation](#-installation) • [✨ Features](#-features) • [📋 Changelog](#-changelog) • [🤝 Support](#-support)

</div>

---

## 🎯 Über ManagerX

ManagerX ist ein leistungsstarker, vielseitiger Discord-Bot, der speziell für umfassendes Community-Management entwickelt wurde. Von automatisierter Moderation über interaktive Levelsysteme bis hin zu globaler Kommunikation – ManagerX bietet alles, was moderne Discord-Server benötigen.

### 🌟 Warum ManagerX?

- ⚡ **Performant** – Optimierte Datenbank und schnelle Antwortzeiten
- 🛡️ **Sicher** – Integriertes Anti-Spam und Moderationstools
- 🎨 **Anpassbar** – Konfigurierbare Features für jeden Server
- 🌍 **Global** – Verbinde deine Community mit der Welt
- 📈 **Aktiv entwickelt** – Regelmäßige Updates und neue Features

---

## ✨ Features

### 🔧 Moderation & Sicherheit

- **Advanced Moderation Tools**
  - Ban, Kick, Mute und weitere Moderationsaktionen
  - Umfangreiches Anti-Spam System mit konfigurierbaren Schwellenwerten
  - Automated Warning-System für Regelverstöße
  - Moderation-Logs für vollständige Transparenz

### 📊 Community Engagement

- **Levelsystem**
  - Vollständig anpassbares XP-System
  - Rollenbelohnungen für Level-Fortschritt
  - Leaderboards und Statistiken
  - Individuelle Level-Up Benachrichtigungen

- **Welcome-System**
  - Automatische Begrüßungsnachrichten
  - Anpassbare Welcome-Embed Designs
  - Regel- und Informationsnachrichten
  - Autorollen für neue Mitglieder

### 🌐 Social & Information

- **Globalchat**
  - Echtzeit-Chat mit anderen Servern weltweit
  - Moderierte und sichere Kommunikation
  - Blacklist-System für Contentfilterung

- **Wikipedia-Integration**
  - Direkte Wikipedia-Suche im Discord
  - Formatierte Artikel-Previews
  - Mehrsprachige Unterstützung

- **Weather-System**
  - Aktuelle Wetterinformationen für beliebige Städte
  - Detaillierte Vorhersagen und Statistiken
  - Automatische Standorterkennung

### 🎮 Interaktive Features

- **Temporary Voice Channels (TempVC)**
  - Nutzer erstellen eigene temporäre Voice-Channel
  - Individuelle Kanalverwaltung und Einstellungen
  - Automatische Löschung bei Inaktivität

- **Globales Stats-System**
  - Server- und nutzerübergreifende Statistiken
  - Performance-Tracking und Analytics
  - Persönliche Erfolge und Meilensteine

---

## 📋 Changelog

### 🚀 Version 1.7.1 (Aktuell)

#### ✨ Major Update
- Umfassende Performance-Optimierungen
- Verbesserte Stabiliät und Fehlerbehandlung
- Erweiterte Konfigurationsmöglichkeiten
- UI/UX Verbesserungen für alle Commands

### 📦 Version 1.7.2 (In Entwicklung)

- 🔜 Neue Moderation-Dashboard Features
- 🔜 Erweiterte Levelsystem-Anpassungen
- 🔜 Optimierte Datenbank-Performance
- 🔜 Weitere Quality-of-Life Verbesserungen

### 🔄 Version 1.6.6

#### 🎯 Levelsystem & Datenbank
- Effizientere Datenspeicherung mit optimierten Queries
- Schnellere XP-Berechnungen und Level-Updates
- Verbesserte Caching-Mechanismen
- Reduzierte Datenbankbelastung bei hoher Aktivität

> 📜 [Vollständiger Changelog](CHANGELOG.md)

---

## 🚀 Installation

### Voraussetzungen

- Python 3.10 oder höher
- Discord Bot Token ([Anleitung](https://discord.com/developers/applications))
- SQLite3 oder kompatible Datenbank

### Quick Start

```bash
# Repository klonen
git clone https://github.com/Oppro-net-Development/ManagerX.git
cd ManagerX

# Abhängigkeiten installieren
pip install -r requirements.txt

# Konfiguration anpassen
.env
# TOKEN Anpassung mehr in unserer Dokumention
# Bot starten
python main.py
```

### 📖 Detaillierte Installation

Eine ausführliche Installationsanleitung findest du in unserer [Dokumentation](docs/INSTALLATION.md).

---

## 🛠️ Konfiguration

ManagerX bietet umfangreiche Konfigurationsmöglichkeiten über die `config.json`:

- **Moderation:** Schwellenwerte, Aktionen, Logs
- **Levelsystem:** XP-Raten, Belohnungen, Level-Kurve
- **Welcome:** Nachrichten, Channels, Rollen
- **Globalchat:** Moderation, Blacklists, Kanäle

> 📘 [Vollständige Konfigurationsdoku](docs/CONFIG.md)

---

## 📝 Commit-Konventionen

Wir nutzen folgende Präfixe für Commits:

| Präfix | Beschreibung | Beispiel |
|--------|--------------|----------|
| `FEATURE:` | Neue Funktion hinzugefügt | `FEATURE: Add weather command` |
| `UPDATE:` | Bestehende Funktion aktualisiert | `UPDATE: Improve levelsystem performance` |
| `BUGFIX:` | Normaler Fehler behoben | `BUGFIX: Fix welcome message formatting` |
| `HOTFIX:` | Kritischer Fehler behoben | `HOTFIX: Resolve database connection issues` |
| `DOCS:` | Dokumentation geändert | `DOCS: Update installation guide` |
| `DELETE:` | Datei oder Feature entfernt | `DELETE: Remove deprecated command` |

---

## 🤝 Support & Community

<div align="center">

### Brauchst du Hilfe oder hast Fragen?

[![Discord Server](https://img.shields.io/badge/Discord_Support-Join_Now-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/tmz673WAnV)
[![Documentation](https://img.shields.io/badge/Documentation-Read_More-00D9FF?style=for-the-badge&logo=gitbook&logoColor=white)](docs/)
[![Issues](https://img.shields.io/badge/GitHub_Issues-Report_Bug-EA4335?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Oppro-net-Development/ManagerX/issues)

</div>

---

## 🏢 Hosting Partner

<div align="center">

### Empfohlener Hosting-Partner für ManagerX

<a href="https://deinserverhost.de/store/aff.php?aff=5609">
  <img src="https://deinserverhost.de/tca/600x150_transparent.png" width="600" height="150" alt="DeinServerHost - Premium Hosting">
</a>

**Zuverlässiges Hosting für Discord Bots und mehr**

[![Zum Angebot](https://img.shields.io/badge/Hosting-Jetzt_buchen-00D9FF?style=for-the-badge&logo=server&logoColor=white)](https://deinserverhost.de/store/aff.php?aff=5609)

</div>

---

## 📄 Lizenz & Urheberrecht

**Copyright © 2024 OPPRO.NET Network**  

---

## 🙏 Credits & Danksagungen

- **Team:** OPPRO.NET Development
- **Community:** Alle Contributors und Tester
- **Frameworks:** py-cord, ezcord
- **Hosting:** DeinServerHost

---

<div align="center">

### ⭐ Hat dir ManagerX geholfen?

**Gib uns einen Star auf GitHub!**

[![GitHub Stars](https://img.shields.io/github/stars/Oppro-net-Development/ManagerX?style=social)](https://github.com/Oppro-net-Development/ManagerX)

---

**Made with ❤️ by OPPRO.NET**

*Bringing communities together, one bot at a time*

</div>
