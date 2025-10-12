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
    ready_event=None
)
# =============================================================================
# BOT VERSION
# =============================================================================
BOT_VERSION = "1.7.1"
VERSION_URL = "https://raw.githubusercontent.com/Oppro-net-Development/ManagerX/main/version.txt"

async def check_for_update():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(VERSION_URL) as resp:
                if resp.status == 200:
                    latest_version = (await resp.text()).strip()
                    if latest_version != BOT_VERSION:
                        print(f"[{Fore.YELLOW}UPDATE{Style.RESET_ALL}] Your Version {BOT_VERSION} is outdated! Latest Version: {latest_version}")
                    else:
                        print(f"[{Fore.GREEN}UP-TO-DATE{Style.RESET_ALL}] You have the latest Version: {BOT_VERSION}")
                else:
                    print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Could not retrieve version, Status: {resp.status}")
    except Exception as e:
        print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Error during update check: {e}")


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
