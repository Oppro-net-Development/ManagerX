# Copyright (c) 2025 OPPRO.NET Network
"""
ManagerX Discord Bot - Main Entry Point
========================================

Version: 1.7.2-alpha
"""

# =============================================================================
# IMPORTS
# =============================================================================
import discord
import os
import asyncio
import logging
import re
import sys
import glob 
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style, init as colorama_init
import aiohttp
import traceback
from log import logger, LogLevel, Category, LogFormat


if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ezcord
from ezcord import log
# ❗ KORRIGIERTER PFAD: DevTools liegt jetzt in src/ vom Root-Verzeichnis aus
from src.DevTools.backend import init_all
from src.handler.update_checker import VersionChecker, UpdateCheckerConfig

# WICHTIG: Lade Environment-Variablen NUR HIER am Anfang
load_dotenv(os.path.join("config", ".env"))

# =============================================================================
# CONFIGURATION
# =============================================================================
class BotConfig:
    """
    Zentrale Bot-Konfiguration.
    """
    VERSION = "1.7.2-alpha"
    VERSION_URL = UpdateCheckerConfig.VERSION_URL
    GITHUB_REPO = UpdateCheckerConfig.GITHUB_REPO
    
    # Intents
    INTENTS = discord.Intents.default()
    INTENTS.members = True
    INTENTS.guilds = True
    INTENTS.messages = True
    INTENTS.message_content = True

logger.configure(
    format_type=LogFormat.SIMPLE
)

# -----------------------------------------------------------------------------
# MESSAGE HANDLER
# -------

class MessageHandler:
    @staticmethod
    def parse_time(text: str) -> int | None:
        match = re.search(r'slowmode\s*(\d+)\s*(s|sec|min|m)?', text.lower())
        if not match:
            return None
        
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit in ("min", "m"):
            return value * 60
        return value
    
    @staticmethod
    async def handle_delete_message(message: discord.Message):
        if not message.reference:
            return False
        
        content_lower = message.content.lower()
        if "lösch das" not in content_lower:
            return False
        
        if not (message.mentions and message.guild.me in message.mentions):
            return False
        
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send(
                f"{message.author.mention} ❌ Du hast keine Berechtigung zum Löschen!",
                delete_after=5
            )
            return True
        
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
            logger.error("MESSAGE", f"Delete failed: {e}")
        
        return True
    
    @staticmethod
    async def handle_slowmode(message: discord.Message):
        content_lower = message.content.lower()
        
        if not (message.mentions and message.guild.me in message.mentions):
            return False
        
        if "slowmode" not in content_lower:
            return False
        
        seconds = MessageHandler.parse_time(content_lower)
        if seconds is None:
            await message.channel.send(
                "❌ Ungültige Zeitangabe!\n"
                "**Beispiele:** `@Bot slowmode 10s`, `@Bot slowmode 5min`",
                delete_after=7
            )
            return True
        
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send(
                f"{message.author.mention} ❌ Du darfst den Slowmode nicht ändern!",
                delete_after=5
            )
            return True
        
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
            logger.error("SLOWMODE", str(e))
        
        return True


# =============================================================================
# BOT CLASS
# =============================================================================
class ManagerXBot(ezcord.Bot):
    
    def __init__(self, config: BotConfig):
        self.config = config
        
        colorama_init(autoreset=True)
        
        ezcord.set_log(
            webhook_url=os.getenv("LOGGING_WEBHOOK_URL"),
        )
        
        super().__init__(
            intents=config.INTENTS,
            language="auto",
            error_webhook_url=os.getenv("ERROR_WEBHOOK_URL"),
            ready_event=None
        )
        
        logger.loading("INIT", "Bot initialized")

    def _load_all_cogs(self):
        """
        Dynamisches Laden aller Cogs basierend auf dem Dateisystem.
        KORREKTUR: Normalisiert die Pfad-Trennung für Windows, damit der 
        Check 'startswith("src.cogs")' funktioniert.
        """
        cogs_dir = "src/cogs"
        
        # Sucht rekursiv nach allen Python-Dateien in Unterordnern von cogs
        cog_files = glob.glob(f"{cogs_dir}/**/[!__]*.py", recursive=True)
        total_cogs = 0

        for file_path in cog_files:
            # 1. Normalisiere den Pfad: Ersetze alle Slashes und Backslashes durch Punkte.
            #    Wir ersetzen zuerst os.path.sep (\ unter Windows) und dann /
            #    Dies stellt sicher, dass der gesamte Pfad in Python-Modulnamen-Konvention umgewandelt wird.
            normalized_path = file_path.replace(os.path.sep, ".").replace("/", ".")
            
            # 2. Entferne die Dateiendung '.py'
            module_name = normalized_path[:-3]
            
            # 3. PRÜFUNG: Stellt sicher, dass der Modulname mit 'src.cogs' beginnt
            if not module_name.startswith("src.cogs"):
                 logger.warn("COGS SKIP", f"Skipping non-standard cog path: {file_path}")
                 continue

            try:
                self.load_extension(module_name)
                logger.info(Category.COGS, f"Loaded: {module_name}")
                total_cogs += 1
            except Exception as e:
                logger.error("COGS FAIL", f"Laden von {module_name} fehlgeschlagen: {e.__class__.__name__}: {e}")
                logger.info("COGS FAIL", "--- Start Traceback ---")
                traceback.print_exc()
                logger.info("COGS FAIL", "--- Ende Traceback ---")
                
        logger.success(Category.COGS, f"Insgesamt {total_cogs} Cogs dynamisch geladen.")
        return total_cogs
    
    async def on_ready(self):
        logger.success("READY", f"Logged in as {self.user}")

        # --- COG LADUNG (Kurzform) ---
        logger.loading(Category.COGS, "Starting dynamic cog loading...")
        self._load_all_cogs()
        # -----------------------------

        
        
        # --- REST DER ON_READY LOGIK FOLGT ---
        
        await VersionChecker.check_update(
            self.config.VERSION,
            self.config.VERSION_URL
        )
        
        await asyncio.sleep(0.5)
        
        try:
            init_all()
            logger.success("DEVTOOLS", "DevTools initialized successfully")
        except Exception as e:
            logger.error("DEVTOOLS", f"Initialization failed: {e}")
        
        await asyncio.sleep(0.5)
        logger.info(Category.SYSTEM, "All systems operational")
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"v{self.config.VERSION} | /help"
            )
        )
    
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        if await MessageHandler.handle_delete_message(message):
            return
        
        if await MessageHandler.handle_slowmode(message):
            return
        
        proc = getattr(self, 'process_commands', None)
        if callable(proc):
            try:
                await proc(message)
            except Exception as e:
                logger.error(Category.COMMANDS, f"process_commands raised: {e}")
    
    def start_bot(self):
        token = os.getenv("TOKEN")
        
        if not token:
            logger.error(Category.AUTH, "Discord bot token not found in environment variables!")
            return
        
        self.add_help_command()
        
        logger.info(Category.BOT, f"Starting ManagerX v{self.config.VERSION}...")
        
        try:
            self.run(token)
        
        except discord.LoginFailure:
            logger.error(Category.AUTH, "Invalid bot token!")
        
        except KeyboardInterrupt:
            logger.warn(Category.SHUTDOWN, "Bot shutdown requested by user")
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    
    # --- DEBUG-CHECK ---
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cogs_test_path = os.path.join(current_dir, "src", "cogs")
        
        logger.info("DEBUG START", f"__file__ dir: {current_dir} (ROOT)")
        logger.info("DEBUG START", f"Cog Path: {cogs_test_path}")
        
        if os.path.exists(cogs_test_path):
            logger.success("DEBUG START", "Cogs Ordner EXISTIERT am erwarteten Pfad!")
        else:
            logger.error("DEBUG START", "Cogs Ordner NICHT gefunden! Pfad ist falsch.")
            
    except Exception as e:
        logger.error(Category.DEBUG, f"Debug check failed: {e}")
    # --- ENDE DEBUG-CHECK ---

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
        logger.error(Category.DEBUG, f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    main()