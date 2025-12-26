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
import json # NEU für Dashboard-Export
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style, init as colorama_init
import aiohttp
import traceback 
from pathlib import Path 
import ezcord
import yaml
from discord.ext import tasks # NEU für Dashboard-Export

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
# DASHBOARD EXPORT TASK (NEU für V2)
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
    # ... (Restliche Checks wie Blacklist) ...

@bot.event
async def on_message(message):
    if message.author.bot: return
    # ... (Anti-Spam Logik) ...

try:
    db = SettingsDB()
    bot.settings_db = db
    logger.info(Category.DATABASE, "Settings Database initialized ✓")
except Exception as e:
    logger.critical(Category.DATABASE, f"Datenbankfehler: {e}")
    sys.exit(1)

# =============================================================================
# COG LOADING LOGIK
# =============================================================================

def get_enabled_cogs(cogs_config):
    enabled_cogs = []
    cog_mapping = {
        'fun': {'gewinnt': 'fun.gewinnt', 'tictactoe': 'fun.tictactoe', 'weather': 'fun.weather', 'wikipedia': 'fun.wikipedia'},
        'information': {'botstatus': 'informationen.botstatus', 'serverinfo': 'informationen.serverinfo', 'usermanagemt': 'informationen.usermanagemt'},
        'moderation': {'antispam': 'moderation.antispam', 'moderation': 'moderation.moderation', 'notes': 'moderation.notes', 'warningsystem': 'moderation.warningsystem'},
        'server_management': {'autodelete': 'Servermanament.autodelete', 'globalchat': 'Servermanament.globalchat', 'levelsystem': 'Servermanament.levelsystem', 'logging': 'Servermanament.logging', 'stats': 'Servermanament.stats', 'tempvc': 'Servermanament.tempvc', 'welcome': 'Servermanament.welcome'},
        'dev_tools': {'logging': 'DevTools.backend.logging', 'emojis': 'DevTools.ui.emojis'},
        'other': {'setlang': 'setlang'}
    }
    for category, cogs in cog_mapping.items():
        category_config = cogs_config.get(category, {})
        for cog_key, module_path in cogs.items():
            if category_config.get(cog_key, True):
                enabled_cogs.append(module_path)
    return enabled_cogs

@bot.event
async def on_ready():
    logger.success(Category.BOT, f"Logged in as {bot.user.name}")
    
    # Dashboard Task starten
    if not update_dashboard_data.is_running():
        update_dashboard_data.start()
        logger.info(Category.STARTUP, "Dashboard Data Export Task gestartet ✓")

    if bot_status_enabled:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"ManagerX v{BotConfig.VERSION}"))

    try:
        loaded_count = 0
        enabled_cogs = get_enabled_cogs(cogs_config)
        cogs_dir_path = BASEDIR / "src" / "cogs"
        cogs_module_path = "src.cogs"
        
        for item in cogs_dir_path.rglob("*.py"):
            if item.name == "__init__.py": continue
            relative_path = item.relative_to(cogs_dir_path).with_suffix('')
            module_name = f"{cogs_module_path}.{str(relative_path).replace(os.sep, '.')}"
            
            if module_name in [f"{cogs_module_path}.{cog}" for cog in enabled_cogs]:
                bot.load_extension(module_name) 
                loaded_count += 1
            
        logger.success(Category.COGS, f"{loaded_count} Cogs geladen.")
        await bot.sync_commands() 
        logger.success(Category.COMMANDS, f"Application Commands synchronisiert.")

    except Exception as e:
        logger.critical(Category.DEBUG, f"Fehler beim Laden: {e}")
        traceback.print_exc()
        sys.exit(1)

    if update_checker_enabled:
        version_checker = VersionChecker()
        asyncio.create_task(version_checker.check_update(current_version=BotConfig.VERSION, version_url="https://raw.githubusercontent.com/Oppro-net-Development/ManagerX/main/config/version.txt"))

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == '__main__':
    print(f"\n{Fore.CYAN}{'=' * 60}\n ManagerX Discord Bot v{BotConfig.VERSION}\n{'=' * 60}{Style.RESET_ALL}\n")
    if not BotConfig.TOKEN:
        logger.critical(Category.DEBUG, "Kein TOKEN gefunden!")
        sys.exit(1)
    bot.run(BotConfig.TOKEN)