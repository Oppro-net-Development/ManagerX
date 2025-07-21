# Copyright (c) 2025 OPPRO.NET Network
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
from FastCoding.backend import init_all

import aiohttp

from ezcord import log



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
time2 = datetime.now().strftime(f"{Fore.CYAN}%H:%M{Style.RESET_ALL}]")
bot = ezcord.Bot(
    intents=intents,
    language="auto", default_language="de",
    logging_level=logging.DEBUG,
    error_webhook_url=os.getenv("ERROR_WEBHOOK_URL"),
    ready_event=None
)

@bot.event
async def on_ready():
    print(f"{time} [{Style.BRIGHT}{Fore.GREEN}STARTING UP{Style.RESET_ALL}] Logged in as {bot.user}")
    await asyncio.sleep(1)
    init_all()
    await asyncio.sleep(1.5)
    print(f"{time} [{Style.BRIGHT}{Fore.LIGHTCYAN_EX}API{Style.RESET_ALL}] Weather API has Loaded.")
    await asyncio.sleep(1.5)
    print(f"{time} [{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}FASTCODING{Style.RESET_ALL}] Fast is ready to use!")



bot.add_help_command()



if __name__ == "__main__":
    # Cogs laden
    bot.load_cogs("cogs", subdirectories=True, custom_log_level =f"{time2} [{Style.BRIGHT}{Fore.RED}COGS LOADING{Style.RESET_ALL}")
    bot.run(os.getenv("TOKEN"))