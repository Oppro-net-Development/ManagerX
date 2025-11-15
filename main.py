# Copyright (c) 2025 OPPRO.NET Network
"""
ManagerX Discord Bot - Main Entry Point
Version: 1.7.2-dev
"""

# =============================================================================
# IMPORTS
# =============================================================================
import discord
import os
import asyncio
import logging
import re
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style, init as colorama_init
import aiohttp

import ezcord
from ezcord import log
from DevTools.backend import init_all

# =============================================================================
# CONFIGURATION
# =============================================================================
class BotConfig:
    """Zentrale Bot-Konfiguration"""
    VERSION = "1.7.2-dev"
    VERSION_URL = "https://raw.githubusercontent.com/Oppro-net-Development/ManagerX/main/version.txt"
    GITHUB_REPO = "https://github.com/Oppro-net-Development/ManagerX"
    
    # Intents
    INTENTS = discord.Intents.default()
    INTENTS.members = True
    INTENTS.guilds = True
    INTENTS.messages = True
    INTENTS.message_content = True
    
    # Logging
    LOG_LEVEL = logging.DEBUG
    DEFAULT_LANGUAGE = "de"


# =============================================================================
# UTILS
# =============================================================================
class ColoredOutput:
    """Formatierte Console-Ausgaben mit Timestamps"""
    
    @staticmethod
    def timestamp() -> str:
        """Gibt einen formatierten Timestamp zurück"""
        return datetime.now().strftime(f"[{Fore.CYAN}%H:%M:%S{Style.RESET_ALL}]")
    
    @staticmethod
    def success(category: str, message: str):
        """Erfolgs-Nachricht"""
        print(f"{ColoredOutput.timestamp()} [{Style.BRIGHT}{Fore.GREEN}{category}{Style.RESET_ALL}] {message}")
    
    @staticmethod
    def error(category: str, message: str):
        """Fehler-Nachricht"""
        print(f"{ColoredOutput.timestamp()} [{Fore.RED}{category}{Style.RESET_ALL}] {message}")
    
    @staticmethod
    def info(category: str, message: str):
        """Info-Nachricht"""
        print(f"{ColoredOutput.timestamp()} [{Style.BRIGHT}{Fore.LIGHTCYAN_EX}{category}{Style.RESET_ALL}] {message}")
    
    @staticmethod
    def warning(category: str, message: str):
        """Warnung"""
        print(f"{ColoredOutput.timestamp()} [{Fore.YELLOW}{category}{Style.RESET_ALL}] {message}")
    
    @staticmethod
    def loading(category: str, message: str):
        """Lade-Nachricht"""
        print(f"{ColoredOutput.timestamp()} [{Style.BRIGHT}{Fore.RED}{category}{Style.RESET_ALL}] {message}")


class VersionChecker:
    """Überprüft Bot-Versionen"""
    
    @staticmethod
    def parse_version(version_str: str) -> tuple:
        """
        Parst Version-String in (major, minor, patch, type)
        Beispiel: "1.7.2-dev" -> (1, 7, 2, "dev")
        """
        match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:[-_]?(dev|beta|alpha))?", version_str)
        if match:
            major, minor, patch, vtype = match.groups()
            return int(major), int(minor), int(patch), vtype or "stable"
        return 0, 0, 0, "unknown"
    
    @staticmethod
    async def check_update(current_version: str, version_url: str) -> str | None:
        """
        Überprüft auf Updates
        Returns: Latest version string oder None bei Fehler
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(version_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        ColoredOutput.error("UPDATE", f"Version check failed (HTTP {resp.status})")
                        return None
                    
                    latest_version = (await resp.text()).strip()
                    if not latest_version:
                        ColoredOutput.error("UPDATE", "Empty response from version server")
                        return None
                    
                    # Versionen vergleichen
                    current = VersionChecker.parse_version(current_version)
                    latest = VersionChecker.parse_version(latest_version)
                    
                    # Status ausgeben
                    if current[:3] == latest[:3] and current[3] == latest[3]:
                        ColoredOutput.success("VERSION", f"Running latest version: {current_version}")
                    
                    elif current[:3] > latest[:3]:
                        ColoredOutput.info(
                            "VERSION",
                            f"Dev build detected ({current_version}) - newer than public release ({latest_version})"
                        )
                    
                    elif current[:3] == latest[:3] and current[3] in ("dev", "beta", "alpha"):
                        ColoredOutput.warning(
                            "VERSION",
                            f"Pre-release version ({current_version}) - latest stable: {latest_version}"
                        )
                    
                    else:
                        print(
                            f"{ColoredOutput.timestamp()} [{Fore.YELLOW}UPDATE AVAILABLE{Style.RESET_ALL}] "
                            f"Current: {current_version} → Latest: {latest_version}\n"
                            f"                    Download: {Fore.CYAN}{BotConfig.GITHUB_REPO}{Style.RESET_ALL}"
                        )
                    
                    return latest_version
        
        except aiohttp.ClientConnectorError:
            ColoredOutput.error("UPDATE", "Could not connect to GitHub (network issue)")
        except asyncio.TimeoutError:
            ColoredOutput.error("UPDATE", "Connection to version server timed out")
        except Exception as e:
            ColoredOutput.error("UPDATE", f"Unexpected error: {e}")
        
        return None


class MessageHandler:
    """Verarbeitet spezielle Message-Commands"""
    
    @staticmethod
    def parse_time(text: str) -> int | None:
        """
        Parst Zeitangaben aus Text
        Beispiele: "10s", "5min", "2m"
        Returns: Sekunden oder None
        """
        match = re.search(r'slowmode\s*(\d+)\s*(s|sec|min|m)?', text.lower())
        if not match:
            return None
        
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit in ("min", "m"):
            return value * 60
        return value  # Sekunden als Standard
    
    @staticmethod
    async def handle_delete_message(message: discord.Message):
        """Verarbeitet 'lösch das' Command"""
        if not message.reference:
            return False
        
        content_lower = message.content.lower()
        if "lösch das" not in content_lower:
            return False
        
        if not (message.mentions and message.guild.me in message.mentions):
            return False
        
        # Permission check
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send(
                f"{message.author.mention} ❌ Du hast keine Berechtigung zum Löschen!",
                delete_after=5
            )
            return True
        
        # Delete message
        try:
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            await replied_msg.delete()
            await message.delete()
            await message.channel.send("✅ Nachricht gelöscht!", delete_after=3)
        except discord.Forbidden:
            await message.channel.send("❌ Keine Berechtigung!", delete_after=5)
        except discord.NotFound:
            await message.channel.send("❌ Nachricht nicht gefunden!", delete_after=5)
        except Exception as e:
            ColoredOutput.error("MESSAGE", f"Delete failed: {e}")
        
        return True
    
    @staticmethod
    async def handle_slowmode(message: discord.Message):
        """Verarbeitet Slowmode Command"""
        content_lower = message.content.lower()
        
        if not (message.mentions and message.guild.me in message.mentions):
            return False
        
        if "slowmode" not in content_lower:
            return False
        
        # Parse time
        seconds = MessageHandler.parse_time(content_lower)
        if seconds is None:
            await message.channel.send(
                "❌ Ungültige Zeitangabe!\n"
                "**Beispiele:** `@Bot slowmode 10s`, `@Bot slowmode 5min`",
                delete_after=7
            )
            return True
        
        # Permission check
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send(
                f"{message.author.mention} ❌ Du darfst den Slowmode nicht ändern!",
                delete_after=5
            )
            return True
        
        # Apply slowmode
        try:
            await message.channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                await message.channel.send("✅ Slowmode deaktiviert!", delete_after=5)
            else:
                time_str = f"{seconds}s" if seconds < 60 else f"{seconds // 60}min"
                await message.channel.send(
                    f"✅ Slowmode auf **{time_str}** gesetzt!",
                    delete_after=5
                )
        except discord.Forbidden:
            await message.channel.send("❌ Keine Berechtigung!", delete_after=5)
        except Exception as e:
            await message.channel.send(f"⚠️ Fehler: {e}", delete_after=5)
            ColoredOutput.error("SLOWMODE", str(e))
        
        return True


# =============================================================================
# BOT CLASS
# =============================================================================
class ManagerXBot(ezcord.Bot):
    """Hauptklasse für den ManagerX Bot"""
    
    def __init__(self, config: BotConfig):
        """Initialisiert den Bot"""
        self.config = config
        
        # Environment laden
        load_dotenv()
        
        # Colorama initialisieren
        colorama_init(autoreset=True)
        
        # ezcord Logging konfigurieren
        ezcord.set_log(
            log_level=config.LOG_LEVEL,
            webhook_url=os.getenv("LOGGING_WEBHOOK_URL"),
        )
        
        # Bot initialisieren
        super().__init__(
            intents=config.INTENTS,
            language="auto",
            default_language=config.DEFAULT_LANGUAGE,
            logging_level=config.LOG_LEVEL,
            error_webhook_url=os.getenv("ERROR_WEBHOOK_URL"),
            ready_event=None
        )
        
        ColoredOutput.loading("INIT", "Bot initialized")
    
    async def setup_hook(self):
        """Setup vor dem Bot-Start"""
        ColoredOutput.info("SETUP", "Running setup hook...")
    
    async def on_ready(self):
        """Event wenn Bot bereit ist"""
        ColoredOutput.success("READY", f"Logged in as {self.user}")
        
        # Version check
        await VersionChecker.check_update(
            self.config.VERSION,
            self.config.VERSION_URL
        )
        
        await asyncio.sleep(0.5)
        
        # DevTools initialisieren
        try:
            init_all()
            ColoredOutput.success("DEVTOOLS", "DevTools initialized successfully")
        except Exception as e:
            ColoredOutput.error("DEVTOOLS", f"Initialization failed: {e}")
        
        await asyncio.sleep(0.5)
        ColoredOutput.info("SYSTEM", "All systems operational")
        
        # Status setzen
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"v{self.config.VERSION} | /help"
            )
        )
    
    async def on_message(self, message: discord.Message):
        """Message Event Handler"""
        # Ignore bots
        if message.author.bot:
            return
        
        # Nur in Guilds
        if not message.guild:
            return
        
        # Special handlers
        if await MessageHandler.handle_delete_message(message):
            return
        
        if await MessageHandler.handle_slowmode(message):
            return
        
        # Process commands
        await self.process_commands(message)
    
    def load_all_cogs(self):
        """Lädt alle Cogs"""
        try:
            ColoredOutput.loading("COGS", "Loading all cogs...")
            
            self.load_cogs(
                "cogs",
                subdirectories=True,
            )
            
            ColoredOutput.success("COGS", "All cogs loaded successfully")
            return True
            
        except Exception as e:
            ColoredOutput.error("COGS", f"Failed to load cogs: {e}")
            return False
    
    def start_bot(self):
        """Startet den Bot"""
        token = os.getenv("TOKEN")
        
        if not token:
            ColoredOutput.error("AUTH", "Discord bot token not found in environment variables!")
            return
        
        # Help Command hinzufügen
        self.add_help_command()
        
        # Cogs laden
        if not self.load_all_cogs():
            ColoredOutput.warning("STARTUP", "Bot starting despite cog errors...")
        
        ColoredOutput.info("BOT", f"Starting ManagerX v{self.config.VERSION}...")
        
        try:
            self.run(token)
        
        except discord.LoginFailure:
            ColoredOutput.error("AUTH", "Invalid bot token!")
        
        except KeyboardInterrupt:
            ColoredOutput.warning("SHUTDOWN", "Bot shutdown requested by user")
        
        except Exception as e:
            ColoredOutput.error("FATAL", f"Unexpected error: {e}")
            raise


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    """Haupteinstiegspunkt"""
    try:
        # Banner ausgeben
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  ManagerX Discord Bot v{BotConfig.VERSION}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  © 2025 OPPRO.NET Network{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
        
        # Bot erstellen und starten
        config = BotConfig()
        bot = ManagerXBot(config)
        bot.start_bot()
    
    except Exception as e:
        ColoredOutput.error("CRITICAL", f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    main()