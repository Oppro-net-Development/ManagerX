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
import asyncio
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv
import ezcord
from ezcord import CogLog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Server, Config

# Logger (muss existieren!)
from logger import logger

# Lokale Module aus src/bot/core
from src.bot.core.config import ConfigLoader, BotConfig
from src.bot.core.bot_setup import BotSetup
from src.bot.core.cog_manager import CogManager
from src.bot.core.database import DatabaseManager
from src.bot.core.dashboard import DashboardTask
from src.bot.core.utils import print_logo

# API Routes für Dashboard
from src.api.dashboard.routes import set_bot_instance, router as dashboard_router

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
# FASTAPI SETUP
# =============================================================================
app = FastAPI(
    title="ManagerX Dashboard API",
    description="Live Bot Status & Statistiken API",
    version=BotConfig.VERSION
)

# CORS aktivieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dashboard-Routes einbinden
app.include_router(dashboard_router)

async def start_webserver():
    """Startet den FastAPI Webserver auf Port 8040"""
    config = Config(app=app, host="0.0.0.0", port=8040, log_level="error")
    server = Server(config)
    await server.serve()
    logger.success("API", "FastAPI-Server läuft auf http://0.0.0.0:8040")

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
    
    # Speichere Bot Start-Zeit für Uptime-Berechnung
    bot.start_time = datetime.utcnow()
    
    # Übergebe Bot-Instanz an die API-Routes
    set_bot_instance(bot)
    logger.info("API", "Bot-Instanz an Dashboard-API übergeben")
    
    # Datenbank initialisieren
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
        
        # --- NEU: Status API & Webserver starten ---
        bot.loop.create_task(start_webserver())
        
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

    # Minimaler KeepAlive Cog
    class KeepAlive(discord.ext.commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @discord.ext.commands.Cog.listener()
        async def on_ready(self):
            logger.info("KEEPALIVE", "KeepAlive Cog aktiv - Bot bleibt online")
    
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