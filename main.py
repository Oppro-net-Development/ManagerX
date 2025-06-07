import discord
from discord.ext import commands, tasks
from discord import slash_command
import os
import random
from dotenv import load_dotenv

import ezcord
import logging


intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
load_dotenv()
bot = ezcord.Bot(
    intents=intents,
    language="de",
    error_webhook_url=os.getenv("ERROR_WEBHOOK_URL"),
)
if __name__ == "__main__":
    bot.load_cogs("cogs", subdirectories=True)
    bot.run(os.getenv("TOKEN"))