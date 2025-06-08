
# ManagerX — Discord Bot Projekt

![ManagerX Logo](https://github.com/Oppro-net-Development/ManagerX/blob/main/GitHub/Img/managerx.png)

---

## Projektstruktur

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
│   ├── moderation/
│   │   ├── Datenbanken/
│   │   │   └── warns.db
│   │   ├── warning-system.py
│   │   ├── admin.py
│   ├── TempVC/
│   │   └── tempvc.py
├── ui/
│   ├── colors.py
│   ├── emojis.py
│   └── templates/
│       └── embeds.py
```

---

## Installation der Abhängigkeiten

```bash
pip install py-cord ezcord python-dotenv
```

---

## main.py — Einstiegspunkt

```python
import os
from dotenv import load_dotenv
import ezcord
import discord

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True

bot = ezcord.Bot(
    intents=intents,
    language="de",
    error_webhook_url=os.getenv("ERROR_WEBHOOK_URL"),
)

if __name__ == "__main__":
    bot.load_cogs("cogs", subdirectories=True)
    bot.run(os.getenv("TOKEN"))
```

---

## Beispiel für einen Cog mit Emojis aus ui/emojis.py

```python
import ezcord
from discord.ext import commands
from ui.emojis import emoji_no  # Beispiel Emoji Import

class BotInfos(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="botinfo", description="Zeigt Informationen zum Bot an")
    async def botinfo(self, ctx):
        await ctx.respond(f"{emoji_no} Hier sind die Bot-Infos!")

def setup(bot):
    bot.add_cog(BotInfos(bot))
```
