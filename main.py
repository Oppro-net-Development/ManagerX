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
from ezcord import CogLog
import yaml
from discord.ext import tasks
from logger import logger, LogLevel, LogFormat, Category 


BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / 'config' / '.env')


# ❗ LOKALE BIBLIOTHEKEN
try:
    from DevTools import SettingsDB 
    
    class BotConfig:
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

# =============================================================================
# COG LOGIK
# =============================================================================

def get_ignored_list(cogs_config):
    """
    Erstellt eine Liste von Dateinamen (ohne .py), die EzCord ignorieren soll.
    """
    # 1. Manuelle Liste von Hilfsdateien, die KEINE Cogs sind
    ignored = [
        "autocomplete", 
        "cache", 
        "components", 
        "config", 
        "containers", 
        "utils",
        "backend", # Falls DevTools Ordner gescannt werden würden
        "emojis"
    ]
    
    # Mapping für Deaktivierung via config.yaml
    # Hier prüfen wir nur, welche Cogs laut Config auf 'false' stehen
    cog_mapping = {
        'fun': {
            'gewinnt': 'gewinnt',
            'tictactoe': 'tictactoe',
            'weather': 'weather',
            'wikipedia': 'cog' # Die Wikipedia Hauptdatei heißt 'cog.py'
        },
        'information': {
            'botstatus': 'botstatus',
            'serverinfo': 'serverinfo',
            'usermanagemt': 'usermanagemt'
        },
        'moderation': {
            'antispam': 'antispam',
            'moderation': 'moderation',
            'notes': 'notes',
            'warningsystem': 'warningsystem'
        },
        'server_management': {
            'autodelete': 'autodelete',
            'globalchat': 'globalchat',
            'levelsystem': 'levelsystem',
            'logging': 'logging',
            'stats': 'stats',
            'tempvc': 'tempvc',
            'welcome': 'welcome'
        },
        'other': {
            'setlang': 'setlang'
        }
    }
    
    for category, cogs in cog_mapping.items():
        category_config = cogs_config.get(category, {})
        for cog_key, file_name in cogs.items():
            if not category_config.get(cog_key, True):
                ignored.append(file_name)
                
    return ignored

# =============================================================================
# BOT INITIALISIERUNG
# =============================================================================

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 

bot = ezcord.Bot(
    intents=intents,
    language="de"
)

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

# =============================================================================
# DASHBOARD EXPORT TASK
# =============================================================================

@tasks.loop(minutes=1)
async def update_dashboard_data():
    try:
        stats = {
            "bot_info": {
                "name": str(bot.user.name),
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
        with open(BASEDIR / 'bot_stats.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)
    except:
        pass

# =============================================================================
# EVENTS
# =============================================================================

@bot.event
async def on_ready():
    logger.success(Category.BOT, f"Logged in as {bot.user.name}")
    if not update_dashboard_data.is_running():
        update_dashboard_data.start()
    
    if bot_status_enabled:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"ManagerX v{BotConfig.VERSION}"))

    await bot.sync_commands()
    logger.success(Category.COMMANDS, "Application Commands synchronisiert.")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == '__main__':
    # Definieren des Logos als Liste von Strings, um Formatierungsprobleme zu umgehe
    logo_lines = [
        r" _____ ______   ________  ________   ________  ________  _______   ________      ___   ___ ",
        r"|\   _ \  _   \|\   __  \|\   ___  \|\   __  \|\   ____\|\  ___ \ |\   __  \    |\  \ /  /|",
        r"\ \  \\\__\ \  \ \  \|\  \ \  \\ \  \ \  \|\  \ \  \___|\ \  __/|\ \  \|\  \   \ \  \/  / /",
        r" \ \  \\|__| \  \ \   __  \ \  \\ \  \ \   __  \ \  \  __\ \  _|/_\ \   _  _\   \ \    / / ",
        r"  \ \  \     \ \  \ \  \ \  \ \  \\ \  \ \  \ \  \ \  \|\  \ \  \_|\ \ \  \\  \|   /     \/  ",
        r"   \ \__\     \ \__\ \__\ \__\ \__\\ \__\ \__\ \__\ \_______\ \_______\ \__\\ _\  /  /\   \  ",
        r"    \|__|      \|__|\|__|\|__|\|__| \|__|\|__|\|__|\|_______|\|_______|\|__|\|__|/__/ /\ __\ ",
        r"                                                                               |__|/ \|__| "
    ]

    # Ausgabe
    print(Fore.CYAN)
    for line in logo_lines:
        print(line)
    print(f"{'=' * 91}")
    print(f" ManagerX Discord Bot v{BotConfig.VERSION}")
    print(f"{'=' * 91}{Style.RESET_ALL}\n")
    
    try:
        db = SettingsDB()
        bot.settings_db = db
        logger.info(Category.DATABASE, "Settings Database initialized ✓")
    except Exception as e:
        logger.critical(Category.DATABASE, f"Datenbankfehler: {e}")

    # --- GEFIXTER LOAD-PROZESS ---
    ignored = get_ignored_list(cogs_config)
    
    bot.load_cogs(
        "src/cogs", 
        subdirectories=True, 
        ignored_cogs=ignored,
        log=CogLog.sum
    )

    if not BotConfig.TOKEN:
        logger.critical(Category.DEBUG, "Kein TOKEN gefunden!")
        import sys
        sys.exit(1)
    
    bot.run(BotConfig.TOKEN)