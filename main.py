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
from pathlib import Path # Path ist wichtig für die rekursive Suche
import ezcord

BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / 'config' / '.env')


# ❗ LOKALE BIBLIOTHEKEN (logger und VersionChecker)
try:
    from log import logger, LogLevel, LogFormat, Category 
    from src.handler.update_checker import VersionChecker 
    from src.DevTools.backend.database.lang_db import SettingsDB 
    
    class BotConfig:
        VERSION = "1.7.2-alpha"
        TOKEN = os.getenv("TOKEN") 
        
except ImportError as e:
    print(f"[{Fore.RED}CRITICAL{Style.RESET_ALL}] [STARTUP] Fataler Fehler beim Import der lokalen Bibliotheken: {e.__class__.__name__}: {e}")
    sys.exit(1)


if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# =============================================================================
# INITIALISIERUNG
# =============================================================================

colorama_init(autoreset=True)

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 

# Bot-Instanz (ohne Cog-Konfiguration, da manuell geladen wird)
bot = ezcord.Bot(
    intents=intents
)


# =============================================================================
# DATENBANK & GLOBALE VARS
# =============================================================================
try:
    db = SettingsDB()
    logger.info(Category.DATABASE, "Settings Database initialized ✓")
    bot.settings_db = db
except Exception as e:
    logger.critical(Category.DATABASE, f"Fehler bei der Datenbankinitialisierung: {e}")
    sys.exit(1)


# =============================================================================
# EVENTS UND COG-LOGIK
# =============================================================================

@bot.event
async def on_ready():
    # --- START BOT READY LOGIK ---
    
    logger.success(Category.BOT, f"Logged in as {bot.user.name}#{bot.user.discriminator}")
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name=f"ManagerX v{BotConfig.VERSION}"))

    # 3. Cog-Laden (DEBUG-MODUS: Absturz wird erzwungen, um Fehler zu finden)
    try:
        loaded_count = 0
        cogs_dir_path = BASEDIR / "src" / "cogs"
        cogs_module_path = "src.cogs"
        
        # Durchlaufe alle .py Dateien rekursiv (auch in Unterordnern)
        for item in cogs_dir_path.rglob("*.py"):
            
            # Überspringe __init__.py oder Dateien, die nicht im cogs_dir_path liegen
            if item.name == "__init__.py" or not item.is_relative_to(cogs_dir_path):
                continue

            # Erstelle den Modulnamen: src.cogs.unterordner.dateiname
            relative_path = item.relative_to(cogs_dir_path).with_suffix('')
            module_name = f"{cogs_module_path}.{str(relative_path).replace(os.sep, '.')}"

            # Lade die Extension OHNE try/except
            logger.info(Category.COGS, f"Versuche zu laden: {module_name}")
            
            # HIER wird der Bot abstürzen, wenn das unsichtbare Zeichen gefunden wird
            bot.load_extension(module_name) 
            loaded_count += 1
            
        logger.success(Category.COGS, f"Insgesamt {loaded_count} Cogs dynamisch geladen.")


        # --- Befehlssynchronisation ---
        logger.info(Category.COMMANDS, "Starting application command synchronization...")
        await bot.sync_commands() 
        synced_commands = bot.application_commands 
        synced_count = len(synced_commands)
        logger.success(Category.COMMANDS, f"✅ Erfolgreich {synced_count} Application Commands synchronisiert.")

    except Exception as e:
        # Dieser Block gibt den genauen Fehler aus und zeigt den Ort des Fehlers
        logger.critical(Category.DEBUG, f"Kritischer Fehler beim Command-Sync/Cog-Laden: {e}")
        print(f"[{Fore.RED}Kritischer Fehler Traceback (Hier suchen!){Style.RESET_ALL}]")
        # DIESER TRACEBACK WIRD DEN GENAUEN ORT DES FEHLERS ZEIGEN
        traceback.print_exc() 
        # Beende den Prozess, da der Bot nicht vollständig starten kann
        sys.exit(1)


    # 4. Version Check und Task-Start
    logger.info(Category.STARTUP, "Starte Version Check")
    version_checker = VersionChecker()
    asyncio.create_task(version_checker.check_update(
        current_version=BotConfig.VERSION,
        version_url="https://raw.githubusercontent.com/Oppro-net-Development/ManagerX/main/config/version.txt"
    ))
    
    # 5. GlobalChat Task-Start
    if globalchat_cog := bot.get_cog("GlobalChatCog"):
        try:
            if hasattr(globalchat_cog, 'cleanup_task') and not globalchat_cog.cleanup_task.is_running():
                globalchat_cog.cleanup_task.start()
        except Exception as e:
            logger.error(Category.DEBUG, f"Fehler beim Start von GlobalChat cleanup_task: {e}")
            
    # --- ENDE BOT READY LOGIK ---


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def debug_check():
    # Ihre bestehende debug_check Funktion
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cogs_test_path = os.path.join(current_dir, "src", "cogs")
        logger.info(Category.DEBUG, f"__file__ dir: {current_dir} (ROOT)") 
        logger.info(Category.DEBUG, f"Cog Path: {cogs_test_path}") 
        if os.path.exists(cogs_test_path):
            logger.success(Category.DEBUG, "Cogs Ordner EXISTIERT am erwarteten Pfad!") 
        else:
            logger.error(Category.DEBUG, "Cogs Ordner NICHT gefunden! Pfad ist falsch.") 
    except Exception as e:
        logger.critical(Category.DEBUG, f"Debug check failed: {e}") 


if __name__ == '__main__':
    
    debug_check()

    try:
        # Banner ausgeben
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN} ManagerX Discord Bot v{BotConfig.VERSION}{Style.RESET_ALL}")
        print(f"{Fore.CYAN} © 2025 OPPRO.NET Network{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

        logger.info(Category.STARTUP, "Bot initialized")
        
        if not BotConfig.TOKEN:
            raise ValueError("Der Bot-Token wurde nicht geladen! Prüfen Sie die .env-Datei (Schlüssel: TOKEN).")

        bot.run(BotConfig.TOKEN)
        
    except ValueError as e:
        logger.critical(Category.DEBUG, str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(Category.BOT, f"Fataler Fehler im Hauptprozess: {e.__class__.__name__}: {e}")
        traceback.print_exc()