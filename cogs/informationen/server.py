import discord
from discord.ext import commands
from discord import slash_command, Option
import ezcord

class ServerInfo(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        description="Zeigt Informationen über den Server an.",
    )
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(
            title=f"Serverinfo für {guild.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="🆔Server-ID", value=guild.id, inline=False)
        embed.add_field(name="👤Mitglieder", value=guild.member_count, inline=False)
        embed.add_field(name="📅Erstellt am", value=guild.created_at.strftime("%d.%m.%Y"), inline=False)
        embed.add_field(name="🔒Besitzer", value=guild.owner.mention, inline=False)
        embed.add_field(name="📈Boost-Level", value=guild.premium_tier, inline=False)
        embed.add_field(name="💎Boosts", value=guild.premium_subscription_count, inline=False)
        embed.add_field(name="🗯️Textkanäle", value=len(guild.text_channels), inline=False)
        embed.add_field(name="🗣️Sprachkanäle", value=len(guild.voice_channels), inline=False)
        embed.add_field(name="📅Emoji-Anzahl", value=len(guild.emojis), inline=False)
        embed.set_footer(text=f"Angefordert von {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        await ctx.send(embed=embed)
def setup(bot):
    bot.add_cog(ServerInfo(bot))