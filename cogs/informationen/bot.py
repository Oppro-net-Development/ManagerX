import discord
from discord.ext import commands
from discord import slash_command, Option
import ezcord

class BotInfos(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        description="Zeigt Informationen über den Bot an."
    )
    async def botinfo(self, ctx):
        embed = discord.Embed(
            title=f"Botinfo für {self.bot.user.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="🆔Bot-ID", value=self.bot.user.id, inline=False)
        embed.add_field(name="📅Erstellt am", value=self.bot.user.created_at.strftime("%d.%m.%Y"), inline=False)
        embed.add_field(name="👤Entwickler", value="LenyPegauOfficial, OPPRO.NET Development", inline=False)
        embed.add_field(name="📈Server", value=len(self.bot.guilds), inline=False)
        embed.add_field(name="💬Kommandoanzahl", value=len(self.bot.commands), inline=False)
        embed.add_field(name="📅weitere bots", value="Radio, ManagerX", inline=False)
        embed.set_footer(text=f"Angefordert von {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(BotInfos(bot))