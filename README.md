<img draggable="false" src="https://github.com/Oppro-net-Development/ManagerX/blob/main/GitHub/Img/managerx.png"></a>


**Aufbau:**
```
ManagerX/
├── main.py
├── .env
├── cogs/
│   ├── informationen/
│   │   ├── bot.py
│   │   ├── botstatus.py
│   │   ├── server.py
│   │   ├── user.py
│   ├── moderation
│   │   ├── Datenbanken
│   │   │   ├── warns.db
│   │   ├── warning-system.py
│   │   ├── admin.py
│   ├── TempVC
│   │   ├── tempvc.py
├── ui/
│   ├── colors.py
│   ├── emojis.py
│   └── templates/
│       └── embeds.py

```
Systeme:
```bash
pip install py-cord ezcord
```
**__main.py aufbau:__**
```python
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
```
Cog aufbau mit emojis aus UI:
```python
import discord
from discord.ext import commands
from discord import slash_command, Option
import ezcord
from ui.emoji import emoji_no

class BotInfos(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(BotInfos(bot))

```
