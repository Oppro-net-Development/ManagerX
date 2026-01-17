"""
ManagerX Discord Bot - Main Entry Point
========================================

Copyright (c) 2025 OPPRO.NET Network
Version: 2.0.0
"""

# =============================================================================
# IMPORTS
# =============================================================================
import discord
import sys
from pathlib import Path
from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv
import ezcord
from ezcord import CogLog

# Logger (muss existieren!)
from logger import logger

# Lokale Module aus src/bot/core
from src.bot.core.config import ConfigLoader, BotConfig
from src.bot.core.bot_setup import BotSetup
from src.bot.core.cog_manager import CogManager
from src.bot.core.database import DatabaseManager
from src.bot.core.dashboard import DashboardTask
from src.bot.core.utils import print_logo

# =============================================================================
# SETUP
# =============================================================================
BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / 'config' / '.env')
colorama_init(autoreset=True)

# Sys-Path
if str(BASEDIR) not in sys.path:
    sys.path.append(str(BASEDIR))

# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == '__main__':
    # Logo ausgeben
    print_logo()
    
    # Konfiguration laden
    logger.info("BOT", "Lade Konfiguration...")
    config_loader = ConfigLoader(BASEDIR)
    config = config_loader.load()
    logger.success("BOT", "Konfiguration geladen")
    
    # Bot erstellen
    logger.info("BOT", "Initialisiere Bot...")
    bot_setup = BotSetup(config)
    bot = bot_setup.create_bot()
    
    # Datenbank initialisieren (optional - Bot läuft auch ohne)
    db_manager = DatabaseManager()
    if not db_manager.initialize(bot):
        logger.warning("DATABASE", "Bot läuft ohne Datenbank weiter...")
    else:
        logger.success("DATABASE", "Datenbank erfolgreich initialisiert")
    
    # Dashboard-Task registrieren
    dashboard = DashboardTask(bot, BASEDIR)
    dashboard.register()
    
    # Event Handler
    @bot.event
    async def on_ready():
        logger.success("BOT", f"Logged in as {bot.user.name}")
        
        # Dashboard starten
        dashboard.start()
        
        # Bot-Status
        if config['features'].get('bot_status', True):
            await bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"ManagerX v{BotConfig.VERSION}"
                )
            )
        
        # Commands sync
        await bot.sync_commands()
        logger.success("COMMANDS", "Application Commands synchronisiert")
    
    # Minimaler KeepAlive Cog - damit Bot immer online bleibt
    class KeepAlive(discord.ext.commands.Cog):
        """Minimal Cog to keep bot online"""
        def __init__(self, bot):
            self.bot = bot
        
        @discord.ext.commands.Cog.listener()
        async def on_ready(self):
            logger.info("KEEPALIVE", "KeepAlive Cog aktiv - Bot bleibt online")
    
    # KeepAlive Cog immer laden
    bot.add_cog(KeepAlive(bot))
    logger.success("BOT", "KeepAlive Cog geladen")
    
    # Cogs laden
    logger.info("BOT", "Lade Cogs...")
    cog_manager = CogManager(config['cogs'])
    ignored = cog_manager.get_ignored_cogs()
    
    bot.load_cogs(
        "src/bot/cogs",
        subdirectories=True,
        ignored_cogs=ignored,
        log=CogLog.sum
    )
    logger.success("BOT", "Cogs geladen")
    
    # Token prüfen
    if not BotConfig.TOKEN:
        logger.critical("DEBUG", "Kein TOKEN in .env gefunden!")
        sys.exit(1)
    
    # Bot starten
    logger.info("BOT", "Starte Bot...")
    try:
        bot.run(BotConfig.TOKEN)
    except discord.LoginFailure:
        logger.critical("BOT", "Ungültiger Token!")
        sys.exit(1)
    except Exception as e:
        logger.critical("BOT", f"Bot-Start fehlgeschlagen: {e}")
        sys.exit(1)