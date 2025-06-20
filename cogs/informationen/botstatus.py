# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────
import discord
from discord.ext import commands, tasks
import ezcord
import math
# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────
class StatusCog(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_status.start()  # Starte den Loop direkt, er pausiert automatisch, falls der Bot nicht bereit ist

    @tasks.loop(seconds=30)
    async def update_status(self):
        if not self.bot.is_ready():
            return

        guild_count = len(self.bot.guilds)
        member_count = sum(g.member_count for g in self.bot.guilds)

        latency = self.bot.latency * 1000
        latency = 0 if math.isnan(latency) else round(latency)

        statuses = [
            f"🌍 {guild_count} | 👥 {member_count} | 🏓 {latency}ms",
        ]
        status_text = statuses[self.update_status.current_loop % len(statuses)]

        await self.bot.change_presence(activity=discord.CustomActivity(name=status_text))

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.update_status.is_running():  # Falls er aus irgendeinem Grund gestoppt wurde
            self.update_status.start()

def setup(bot):
    bot.add_cog(StatusCog(bot))