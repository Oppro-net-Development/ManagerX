# Copyright (c) 2025 OPPRO.NET Network
# =============================================================================
# IMPORTS
# =============================================================================
import discord
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
from colorama import Fore, Style
import asyncio
import ezcord
import logging
from discord.ext import tasks
from DevTools.backend import init_all
import yaml
import aiohttp
import random
from ezcord import log
import re

import yaml
# =============================================================================
# CODE & COMMANDS
# =============================================================================

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True
load_dotenv()

ezcord.set_log(
    log_level=logging.DEBUG,
    webhook_url=os.getenv("LOGGING_WEBHOOK_URL"),
)


time = datetime.now().strftime(f"[{Fore.CYAN}%H:%M{Style.RESET_ALL}]")
time2 = datetime.now().strftime(f"[{Fore.CYAN}%H:%M{Style.RESET_ALL}]")
bot = ezcord.Bot(
    intents=intents,
    language="auto", default_language="de",
    logging_level=logging.DEBUG,
    error_webhook_url=os.getenv("ERROR_WEBHOOK_URL"),
    ready_event=None,
    debug_guild=1428835818792947884
)
# =============================================================================
# BOT VERSION
# =============================================================================
import aiohttp
from colorama import Fore, Style
import re

BOT_VERSION = "1.7.2-dev"
VERSION_URL = "https://raw.githubusercontent.com/Oppro-net-Development/ManagerX/main/version.txt"


def parse_version(v: str):
    """Zerlegt Version in (major, minor, patch, type)"""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:[-_]?(dev|beta))?", v)
    if match:
        major, minor, patch, vtype = match.groups()
        return int(major), int(minor), int(patch), vtype or "stable"
    return 0, 0, 0, "unknown"


async def check_for_update():
    """Überprüft, ob eine neuere Version verfügbar ist oder ob du eine Dev-/Beta-Version nutzt."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(VERSION_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Update check failed (HTTP {resp.status})")
                    return None

                latest_version = (await resp.text()).strip()
                if not latest_version:
                    print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Empty response from version server!")
                    return None

                # Versionen parsen
                current = parse_version(BOT_VERSION)
                latest = parse_version(latest_version)

                # --- Vergleich ---
                if current[:3] == latest[:3] and current[3] == latest[3]:
                    print(f"[{Fore.GREEN}UP-TO-DATE{Style.RESET_ALL}] Running latest version: {BOT_VERSION}")

                elif current[:3] > latest[:3]:
                    print(
                        f"[{Fore.CYAN}DEV BUILD{Style.RESET_ALL}] "
                        f"Your version ({BOT_VERSION}) is newer than the latest public release ({latest_version})!"
                    )

                elif current[:3] == latest[:3] and current[3] in ("dev", "beta"):
                    print(
                        f"[{Fore.MAGENTA}PRE-RELEASE{Style.RESET_ALL}] "
                        f"You are using a {current[3].upper()} version ({BOT_VERSION}) — "
                        f"latest stable: {latest_version}"
                    )

                else:
                    print(
                        f"[{Fore.YELLOW}UPDATE AVAILABLE{Style.RESET_ALL}] "
                        f"Installed: {BOT_VERSION} → Latest: {latest_version}\n"
                        f"Get the latest version here: {Fore.CYAN}https://github.com/Oppro-net-Development/ManagerX{Style.RESET_ALL}"
                    )

                return latest_version

    except aiohttp.ClientConnectorError:
        print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Could not connect to GitHub (network issue).")
    except aiohttp.ServerTimeoutError:
        print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Connection to version server timed out.")
    except Exception as e:
        print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Unexpected error: {e}")

    return None




@bot.event
async def on_ready():
    print(f"{time} [{Style.BRIGHT}{Fore.GREEN}STARTING UP{Style.RESET_ALL}] Logged in as {bot.user}")
    await check_for_update()
    await asyncio.sleep(1)
    init_all()
    await asyncio.sleep(1.5)
    print(f"{time} [{Style.BRIGHT}{Fore.LIGHTCYAN_EX}API{Style.RESET_ALL}] Weather API has Loaded.")
    await asyncio.sleep(1.5)
    print(f"{time} [{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}DEVTOOLS{Style.RESET_ALL}] DevTools is ready to use!")

def parse_time(text: str) -> int:
    # Sucht nach Zahl+Einheit direkt hinter slowmode oder irgendwo im Text
    match = re.search(r'slowmode\s*(\d+)(s|min|m)?', text.lower())
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    if unit in ("min", "m"):
        return value * 60
    return value  # Sekunden standardmäßig
# =============================================================================
# MESSAGE CONTENT
# =============================================================================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content_lower = message.content.lower()

    # 1. "Antwort + lösch das"
    if message.reference and "lösch das" in content_lower:
        if message.mentions and bot.user in message.mentions:
            if not message.author.guild_permissions.manage_messages:
                await message.channel.send(f"{message.author.mention}, du hast keine Berechtigung zum Löschen!", delete_after=5)
                return
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
                await replied_message.delete()
                await message.delete()
                await message.channel.send("✅ Nachricht gelöscht!", delete_after=3)
            except Exception as e:
                print(f"Fehler beim Löschen: {e}")
        return  # Wichtig: sonst können weitere Checks doppelt reagieren

    # 2. Slowmode setzen bei Nachricht an Bot mit slowmode
    if message.mentions and bot.user in message.mentions and "slowmode" in content_lower:
        seconds = parse_time(content_lower)
        if seconds is None:
            await message.channel.send("❌ Ungültige Zeitangabe! Nutze z. B. `10s`, `1min` etc.", delete_after=5)
            return
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send("🚫 Du darfst den Slowmode nicht ändern!", delete_after=5)
            return
        try:
            await message.channel.edit(slowmode_delay=seconds)
            await message.channel.send(f"✅ Slowmode auf `{seconds}` Sekunden gesetzt!", delete_after=5)
        except Exception as e:
            await message.channel.send(f"⚠️ Fehler: {e}", delete_after=5)
        return  # wichtig für andere Befehle
# =============================================================================
# Übersetzung
# =============================================================================

with open("translation/messages/de.yaml", encoding="utf-8") as file:
    de = yaml.safe_load(file)

with open("translation/messages/en.yaml", encoding="utf-8") as file:
    en = yaml.safe_load(file)

ezcord.I18N({"de": de, "en": en}, prefer_user_locale=True, fallback_locale="en")


# =============================================================================
# BOT START
# =============================================================================
def main():
    token = os.getenv("TOKEN")
    if not token:
        print(f"{time} [{Fore.RED}ERROR{Style.RESET_ALL}] "
              "Discord bot token not found in environment variables!")
        return
    
    bot.add_help_command()
    
    # Load cog
    try:
        bot.load_cogs(
            "cogs",
            subdirectories=True,
            custom_log_level=f"{time2} [{Style.BRIGHT}{Fore.RED}COGS LOADING{Style.RESET_ALL}"
        )
        print(f"{time2} [{Style.BRIGHT}{Fore.GREEN}COGS{Style.RESET_ALL}] "
              "All cogs loaded successfully")
    except Exception as error:
        print(f"{time2} [{Fore.RED}ERROR{Style.RESET_ALL}] "
              f"Failed to load cogs: {error}")
    
    print(f"{time} [{Style.BRIGHT}{Fore.BLUE}BOT{Style.RESET_ALL}] "
          "Starting ManagerX...")
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        print(f"{time} [{Fore.RED}ERROR{Style.RESET_ALL}] "
              "Invalid bot token!")
    except KeyboardInterrupt:
        print(f"\n{time} [{Fore.YELLOW}SHUTDOWN{Style.RESET_ALL}] "
              "Bot shutdown requested")
    except Exception as error:
        print(f"{time} [{Fore.RED}ERROR{Style.RESET_ALL}] "
              f"Unexpected error: {error}")

if __name__ == "__main__":
    main()