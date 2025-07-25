import discord
from discord.ext import commands
import datetime


class ServerInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Zeigt Discord-Server Informationen an")
    async def serverinfo(self, ctx):
        guild = ctx.guild

        # Server-Statistiken sammeln
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bots = len([m for m in guild.members if m.bot])
        humans = total_members - bots

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        roles = len(guild.roles)
        emojis = len(guild.emojis)

        embed = discord.Embed(
            title=f"📊 Server Info: {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Basis-Infos
        embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Erstellt am", value=guild.created_at.strftime("%d.%m.%Y"), inline=True)

        # Mitglieder
        embed.add_field(
            name="👥 Mitglieder",
            value=f"**Gesamt:** {total_members}\n**Menschen:** {humans}\n**Bots:** {bots}\n**Online:** {online_members}",
            inline=True
        )

        # Kanäle
        embed.add_field(
            name="📺 Kanäle",
            value=f"**Text:** {text_channels}\n**Voice:** {voice_channels}\n**Kategorien:** {categories}",
            inline=True
        )

        # Weitere Infos
        embed.add_field(
            name="🎭 Server Features",
            value=f"**Rollen:** {roles}\n**Emojis:** {emojis}\n**Boosts:** {guild.premium_subscription_count}",
            inline=True
        )

        # Sicherheit
        embed.add_field(name="🛡️ Verifikation", value=guild.verification_level.name.title(), inline=True)
        embed.add_field(name="📊 Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="🔒 MFA Level", value="Aktiviert" if guild.mfa_level else "Deaktiviert", inline=True)

        embed.set_footer(text=f"Angefragt von {ctx.author}",
                         icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(ServerInfoCog(bot))