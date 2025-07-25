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
import yaml
import aiohttp
import random
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


antworten = [
    ("Wer stört mich bei der Arbeit?", 21),
    ("Ja? Was gibt's?", 21),
    ("Ich bin beschäftigt, aber gut…", 23),
    ("Sprich schnell, ich hab nicht ewig Zeit 😤", 35)
]

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        antwort = weighted_choice(antworten)
        await message.channel.send(antwort)

def weighted_choice(choices):
    total = sum(weight for _, weight in choices)
    r = random.randint(1, total)
    upto = 0
    for choice, weight in choices:
        upto += weight
        if r <= upto:
            return choice
if __name__ == "__main__":
    # Cogs laden
    bot.load_cogs("cogs", subdirectories=True, custom_log_level =f"{time2} [{Style.BRIGHT}{Fore.RED}COGS LOADING{Style.RESET_ALL}")
    bot.run(os.getenv("TOKEN"))