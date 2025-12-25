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
import yaml

BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / 'config' / '.env')


# ❗ LOKALE BIBLIOTHEKEN (logger und VersionChecker)
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
# INITIALISIERUNG
# =============================================================================

colorama_init(autoreset=True)

# Lade Konfiguration aus config.yaml
config_path = BASEDIR / 'config' / 'config.yaml'
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Prüfe, ob das System aktiviert ist
    if not config.get('enabled', True):
        print(f"[{Fore.YELLOW}INFO{Style.RESET_ALL}] Bot ist in config.yaml deaktiviert. Beende...")
        sys.exit(0)
    
    # Setze Version aus Config
    config_version = config.get('version', '1.0.0')
    BotConfig.VERSION = config_version
    print(f"[{Fore.GREEN}INFO{Style.RESET_ALL}] Bot Version aus config.yaml geladen: {BotConfig.VERSION}")
    
    # Features aus Config
    features = config.get('features', {})
    update_checker_enabled = features.get('update_checker', True)
    bot_status_enabled = features.get('bot_status', True)
    cogs_config = features.get('cogs', {})
    
    # Bot-Verhalten
    bot_behavior = config.get('bot_behavior', {})
    command_prefix = bot_behavior.get('command_prefix', '!')
    global_cooldown = bot_behavior.get('global_cooldown_seconds', 5)
    max_messages_per_minute = bot_behavior.get('max_messages_per_minute', 10)
    maintenance_mode = bot_behavior.get('maintenance_mode', False)
    
    # UI
    ui_config = config.get('ui', {})
    embed_color = ui_config.get('embed_color', '#00ff00')
    footer_text = ui_config.get('footer_text', 'ManagerX Bot')
    theme = ui_config.get('theme', 'dark')
    show_timestamps = ui_config.get('show_timestamps', True)
    
    # Sicherheit
    security_config = config.get('security', {})
    required_permissions = security_config.get('required_permissions', [])
    blacklist_servers = security_config.get('blacklist_servers', [])
    whitelist_users = security_config.get('whitelist_users', [])
    enable_command_logging = security_config.get('enable_command_logging', True)
    
    # Performance
    performance_config = config.get('performance', {})
    max_concurrent_tasks = performance_config.get('max_concurrent_tasks', 10)
    task_timeout = performance_config.get('task_timeout_seconds', 30)
    memory_limit = performance_config.get('memory_limit_mb', 512)
    enable_gc_optimization = performance_config.get('enable_gc_optimization', True)
    
except FileNotFoundError:
    print(f"[{Fore.YELLOW}WARN{Style.RESET_ALL}] config.yaml nicht gefunden. Verwende Standardwerte.")
    config = {}
    features = {}
    update_checker_enabled = True
    bot_status_enabled = True
    cogs_config = {}
    # Standardwerte für neue Optionen
    command_prefix = '!'
    global_cooldown = 5
    max_messages_per_minute = 10
    maintenance_mode = False
    embed_color = '#00ff00'
    footer_text = 'ManagerX Bot'
    theme = 'dark'
    show_timestamps = True
    required_permissions = []
    blacklist_servers = []
    whitelist_users = []
    enable_command_logging = True
    max_concurrent_tasks = 10
    task_timeout = 30
    memory_limit = 512
    enable_gc_optimization = True
except Exception as e:
    print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Fehler beim Laden der config.yaml: {e}")
    sys.exit(1)

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 

# Bot-Instanz (ohne Cog-Konfiguration, da manuell geladen wird)
bot = ezcord.Bot(
    intents=intents
)

# Speichere Config-Werte im Bot-Objekt für globale Zugriffe
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

# Globale Variablen für Cooldowns und Message-Tracking
user_cooldowns = {}
user_message_counts = {}


# =============================================================================
# EVENTS FÜR BOT-VERHALTEN
# =============================================================================

@bot.event
async def on_application_command(ctx):
    # Maintenance Mode prüfen
    if bot.config['maintenance_mode']:
        await ctx.respond("🚧 Der Bot befindet sich im Wartungsmodus. Bitte versuche es später erneut.", ephemeral=True)
        return
    
    # Blacklist prüfen
    if ctx.guild and ctx.guild.id in bot.config['blacklist_servers']:
        await ctx.respond("❌ Dieser Server ist blockiert.", ephemeral=True)
        return
    if bot.config['whitelist_users'] and ctx.user.id not in bot.config['whitelist_users']:
        await ctx.respond("❌ Du bist nicht berechtigt, diesen Bot zu verwenden.", ephemeral=True)
        return
    
    # Global Cooldown prüfen
    now = datetime.now()
    user_id = ctx.user.id
    if user_id in user_cooldowns:
        time_diff = (now - user_cooldowns[user_id]).total_seconds()
        if time_diff < bot.config['global_cooldown']:
            remaining = bot.config['global_cooldown'] - time_diff
            await ctx.respond(f"⏳ Bitte warte {remaining:.1f} Sekunden vor dem nächsten Command.", ephemeral=True)
            return
    user_cooldowns[user_id] = now
    
    # Command Logging
    if bot.config['enable_command_logging']:
        logger.info(Category.COMMANDS, f"Command ausgeführt: {ctx.command.name} von {ctx.user.name}#{ctx.user.discriminator} in {ctx.guild.name if ctx.guild else 'DM'}")

@bot.event
async def on_message(message):
    # Message-Tracking für Anti-Spam (einfach)
    if message.author.bot:
        return
    
    user_id = message.author.id
    now = datetime.now()
    
    if user_id not in user_message_counts:
        user_message_counts[user_id] = []
    
    # Entferne alte Messages (älter als 1 Minute)
    user_message_counts[user_id] = [t for t in user_message_counts[user_id] if (now - t).total_seconds() < 60]
    user_message_counts[user_id].append(now)
    
    if len(user_message_counts[user_id]) > bot.config['max_messages_per_minute']:
        # Hier könntest du eine Warnung oder Timeout senden, aber für jetzt nur loggen
        logger.warning(Category.SECURITY, f"User {message.author.name} überschreitet Message-Limit ({len(user_message_counts[user_id])}/min)")


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
# CONFIG-BASED COG LOADING
# =============================================================================

def get_enabled_cogs(cogs_config):
    """Bestimme welche Cogs basierend auf der Config geladen werden sollen."""
    enabled_cogs = []
    
    # Mapping von Config-Schlüsseln zu Dateipfaden
    cog_mapping = {
        'fun': {
            'gewinnt': 'fun.gewinnt',
            'tictactoe': 'fun.tictactoe',
            'weather': 'fun.weather',
            'wikipedia': 'fun.wikipedia'
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
            if category_config.get(cog_key, True):  # Standardmäßig aktiviert
                enabled_cogs.append(module_path)
    
    return enabled_cogs


# =============================================================================
# EVENTS UND COG-LOGIK
# =============================================================================

@bot.event
async def on_ready():
    # --- START BOT READY LOGIK ---
    
    logger.success(Category.BOT, f"Logged in as {bot.user.name}#{bot.user.discriminator}")
    
    # Setze Presence basierend auf Config
    if bot_status_enabled:
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name=f"ManagerX v{BotConfig.VERSION}"))
    else:
        await bot.change_presence(activity=None)

    # 3. Cog-Laden basierend auf Config
    try:
        loaded_count = 0
        enabled_cogs = get_enabled_cogs(cogs_config)
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
            
            # Prüfe, ob dieser Cog aktiviert ist
            if module_name not in [f"{cogs_module_path}.{cog}" for cog in enabled_cogs]:
                logger.info(Category.COGS, f"Überspringe deaktivierten Cog: {module_name}")
                continue

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


    # 4. Version Check und Task-Start (nur wenn aktiviert)
    if update_checker_enabled:
        logger.info(Category.STARTUP, "Starte Version Check")
        version_checker = VersionChecker()
        asyncio.create_task(version_checker.check_update(
            current_version=BotConfig.VERSION,
            version_url="https://raw.githubusercontent.com/Oppro-net-Development/ManagerX/main/config/version.txt"
        ))
    else:
        logger.info(Category.STARTUP, "Update Checker deaktiviert in config.yaml")
    
    # 5. GlobalChat Task-Start (nur wenn GlobalChat Cog geladen)
            
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