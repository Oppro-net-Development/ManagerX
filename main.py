# Copyright (c) 2025 OPPRO.NET Network
"""
ManagerX Discord Bot - Main Entry Point
========================================

Version: 2.0.0
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
import json
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style, init as colorama_init
import aiohttp
import traceback 
from pathlib import Path 
import ezcord
import yaml
from discord.ext import tasks

BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / 'config' / '.env')


# ❗ LOKALE BIBLIOTHEKEN
try:
    from log import logger, LogLevel, LogFormat, Category 
    from src.handler.update_checker import VersionChecker 
    from src.DevTools.backend.database.lang_db import SettingsDB 
    
    class BotConfig:
        VERSION = "2.0.0-dev"
        TOKEN = os.getenv("TOKEN") 
        
except ImportError as e:
    print(f"[{Fore.RED}CRITICAL{Style.RESET_ALL}] [STARTUP] Fataler Fehler beim Import der lokalen Bibliotheken: {e.__class__.__name__}: {e}")
    sys.exit(1)


if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# =============================================================================
# INITIALISIERUNG & CONFIG LOADING
# =============================================================================

colorama_init(autoreset=True)

config_path = BASEDIR / 'config' / 'config.yaml'
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if not config.get('enabled', True):
        print(f"[{Fore.YELLOW}INFO{Style.RESET_ALL}] Bot ist in config.yaml deaktiviert. Beende...")
        sys.exit(0)
    
    config_version = config.get('version', '1.0.0')
    BotConfig.VERSION = config_version
    
    features = config.get('features', {})
    update_checker_enabled = features.get('update_checker', True)
    bot_status_enabled = features.get('bot_status', True)
    cogs_config = features.get('cogs', {})
    
    bot_behavior = config.get('bot_behavior', {})
    command_prefix = bot_behavior.get('command_prefix', '!')
    global_cooldown = bot_behavior.get('global_cooldown_seconds', 5)
    max_messages_per_minute = bot_behavior.get('max_messages_per_minute', 10)
    maintenance_mode = bot_behavior.get('maintenance_mode', False)
    
    ui_config = config.get('ui', {})
    embed_color = ui_config.get('embed_color', '#00ff00')
    footer_text = ui_config.get('footer_text', 'ManagerX Bot')
    theme = ui_config.get('theme', 'dark')
    show_timestamps = ui_config.get('show_timestamps', True)
    
    security_config = config.get('security', {})
    required_permissions = security_config.get('required_permissions', [])
    blacklist_servers = security_config.get('blacklist_servers', [])
    whitelist_users = security_config.get('whitelist_users', [])
    enable_command_logging = security_config.get('enable_command_logging', True)
    
    performance_config = config.get('performance', {})
    max_concurrent_tasks = performance_config.get('max_concurrent_tasks', 10)
    task_timeout = performance_config.get('task_timeout_seconds', 30)
    memory_limit = performance_config.get('memory_limit_mb', 512)
    enable_gc_optimization = performance_config.get('enable_gc_optimization', True)
    
except Exception as e:
    print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Fehler beim Laden der config.yaml: {e}")
    sys.exit(1)

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 

bot = ezcord.Bot(intents=intents)

bot.config = {
    'embed_color': embed_color,
    'footer_text': footer_text,
    'theme': theme,
    'show_timestamps': show_timestamps,
    'maintenance_mode': maintenance_mode,
    'global_cooldown': global_cooldown,
    'max_messages_per_minute': max_messages_per_minute,
    'required_permissions': required_permissions,
    'blacklist_servers': blacklist_servers,
    'whitelist_users': whitelist_users,
    'enable_command_logging': enable_command_logging,
    'max_concurrent_tasks': max_concurrent_tasks,
    'task_timeout': task_timeout,
    'memory_limit': memory_limit,
    'enable_gc_optimization': enable_gc_optimization
}

user_cooldowns = {}
user_message_counts = {}

# =============================================================================
# DASHBOARD EXPORT TASK
# =============================================================================

@tasks.loop(minutes=1)
async def update_dashboard_data():
    """Exportiert Live-Statistiken für die api.py."""
    try:
        stats = {
            "bot_info": {
                "name": str(bot.user.name),
                "version": BotConfig.VERSION,
                "status": "online",
                "latency": round(bot.latency * 1000, 1)
            },
            "stats": {
                "server_count": len(bot.guilds),
                "user_count": sum(g.member_count for g in bot.guilds if g.member_count),
                "shards": bot.shard_count or 1
            },
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        stats_path = BASEDIR / 'bot_stats.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        if hasattr(logger, 'error'):
            logger.error(Category.BOT, f"Dashboard-Export fehlgeschlagen: {e}")

# =============================================================================
# EVENTS
# =============================================================================

@bot.event
async def on_application_command(ctx):
    if bot.config['maintenance_mode']:
        await ctx.respond("🚧 Der Bot befindet sich im Wartungsmodus.", ephemeral=True)
        return

@bot.event
async def on_message(message):
    if message.author.bot: 
        return

try:
    db = SettingsDB()
    bot.settings_db = db
    logger.info(Category.DATABASE, "Settings Database initialized ✓")
except Exception as e:
    logger.critical(Category.DATABASE, f"Datenbankfehler: {e}")
    sys.exit(1)

# =============================================================================
# COG LOADING LOGIK - ANGEPASST FÜR WIKIPEDIA PACKAGE
# =============================================================================

def get_enabled_cogs(cogs_config):
    """
    Gibt eine Liste der aktivierten Cogs zurück.
    Unterstützt jetzt auch Package-basierte Cogs (wie wikipedia).
    """
    enabled_cogs = []
    
    # Mapping von config.yaml Keys zu Modul-Pfaden
    cog_mapping = {
        'fun': {
            'gewinnt': 'fun.gewinnt',
            'tictactoe': 'fun.tictactoe',
            'weather': 'fun.weather',
            'wikipedia': 'fun.wikipedia.cog'  # Package -> direkt zu cog.py
        },
        'information': {
            'botstatus': 'informationen.botstatus',
            'serverinfo': 'informationen.serverinfo',
            'usermanagemt': 'informationen.usermanagemt'
        },
        'moderation': {
            'antispam': 'moderation.antispam',
            'moderation': 'moderation.moderation',
            'notes': 'moderation.notes',
            'warningsystem': 'moderation.warningsystem'
        },
        'server_management': {
            'autodelete': 'Servermanament.autodelete',
            'globalchat': 'Servermanament.globalchat',
            'levelsystem': 'Servermanament.levelsystem',
            'logging': 'Servermanament.logging',
            'stats': 'Servermanament.stats',
            'tempvc': 'Servermanament.tempvc',
            'welcome': 'Servermanament.welcome'
        },
        'dev_tools': {
            'logging': 'DevTools.backend.logging',
            'emojis': 'DevTools.ui.emojis'
        },
        'other': {
            'setlang': 'setlang'
        }
    }
    
    for category, cogs in cog_mapping.items():
        category_config = cogs_config.get(category, {})
        for cog_key, module_path in cogs.items():
            # Prüfen ob der Cog in der Config aktiviert ist (Standard: True)
            if category_config.get(cog_key, True):
                enabled_cogs.append(module_path)
                
    return enabled_cogs

def is_cog_enabled(module_path, enabled_cogs, cogs_module_path):
    """
    Prüft ob ein Cog aktiviert ist.
    Unterstützt sowohl Einzeldateien als auch Packages.
    """
    full_module = f"{cogs_module_path}.{module_path}"
    
    # Direkter Match
    if full_module in [f"{cogs_module_path}.{cog}" for cog in enabled_cogs]:
        return True
    
    # Package-Match (z.B. wikipedia/__init__.py sollte geladen werden wenn fun.wikipedia aktiviert ist)
    for enabled_cog in enabled_cogs:
        enabled_full = f"{cogs_module_path}.{enabled_cog}"
        # Wenn module_path ein Untermodul eines aktivierten Packages ist
        if full_module.startswith(enabled_full):
            return True
            
    return False

@bot.event
async def on_ready():
    logger.success(Category.BOT, f"Logged in as {bot.user.name}")
    
    # Dashboard Task starten
    if not update_dashboard_data.is_running():
        update_dashboard_data.start()
        logger.info(Category.STARTUP, "Dashboard Data Export Task gestartet ✓")

    if bot_status_enabled:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name=f"ManagerX v{BotConfig.VERSION}"
            )
        )

    try:
        loaded_count = 0
        skipped_count = 0
        enabled_cogs = get_enabled_cogs(cogs_config)
        cogs_dir_path = BASEDIR / "src" / "cogs"
        cogs_module_path = "src.cogs"
        
        # Alle Python-Dateien im cogs-Verzeichnis finden
        for item in cogs_dir_path.rglob("*.py"):
            # __init__.py und __pycache__ überspringen
            if item.name == "__init__.py" or "__pycache__" in str(item):
                continue
                
            # Relativen Pfad berechnen
            relative_path = item.relative_to(cogs_dir_path).with_suffix('')
            module_path = str(relative_path).replace(os.sep, '.')
            full_module_name = f"{cogs_module_path}.{module_path}"
            
            # Debugging-Output
            logger.debug(Category.DEBUG, f"Gefundene Datei: {module_path}")
            
            # Prüfen ob der Cog aktiviert ist
            if is_cog_enabled(module_path, enabled_cogs, cogs_module_path):
                try:
                    bot.load_extension(full_module_name)
                    loaded_count += 1
                    logger.info(Category.COGS, f"✓ Geladen: {module_path}")
                except Exception as e:
                    logger.error(Category.COGS, f"✗ Fehler beim Laden von {module_path}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                skipped_count += 1
                logger.debug(Category.COGS, f"⊘ Übersprungen (deaktiviert): {module_path}")
        
        logger.success(Category.COGS, f"{loaded_count} Cogs geladen, {skipped_count} übersprungen.")
        
        # Commands synchronisieren
        await bot.sync_commands()
        logger.success(Category.COMMANDS, "Application Commands synchronisiert.")

    except Exception as e:
        logger.critical(Category.DEBUG, f"Fehler beim Laden: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Update Checker
    if update_checker_enabled:
        version_checker = VersionChecker()
        asyncio.create_task(
            version_checker.check_update(
                current_version=BotConfig.VERSION,
                version_url="https://raw.githubusercontent.com/Oppro-net-Development/ManagerX/main/config/version.txt"
            )
        )

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == '__main__':
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f" ManagerX Discord Bot v{BotConfig.VERSION}")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")
    
    if not BotConfig.TOKEN:
        logger.critical(Category.DEBUG, "Kein TOKEN gefunden!")
        sys.exit(1)
        
    bot.run(BotConfig.TOKEN)