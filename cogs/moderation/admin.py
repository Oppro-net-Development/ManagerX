import discord
from discord.ext import commands
from discord import option
from datetime import timedelta
import ezcord

from ui.emojis import emoji_no, emoji_yes, emoji_user

class Moderation(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ✅ Ban Command
    @commands.slash_command(name="ban", description="Bannt ein Mitglied")
    @option("member", discord.Member, description="Wen willst du bannen?")
    @option("reason", str, description="Grund für den Bann", required=False)
    async def ban(self, ctx: discord.ApplicationContext, member: discord.Member, reason: str = "Kein Grund angegeben"):
        if not ctx.author.guild_permissions.ban_members:
            return await ctx.respond(f"{emoji_no} Du brauchst die Berechtigung 'Mitglieder bannen'.", ephemeral=True)

        try:
            await member.ban(reason=reason)
            await ctx.respond(f"{emoji_yes} {emoji_user}{member.mention} wurde gebannt.\nGrund: {reason}")
        except discord.Forbidden:
            await ctx.respond(f"{emoji_no} Ich kann dieses Mitglied nicht bannen.", ephemeral=True)

    # ✅ Kick Command
    @commands.slash_command(name="kick", description="Kickt ein Mitglied")
    @option("member", discord.Member, description="Wen willst du kicken?")
    @option("reason", str, description="Grund für den Kick", required=False)
    async def kick(self, ctx: discord.ApplicationContext, member: discord.Member, reason: str = "Kein Grund angegeben"):
        if not ctx.author.guild_permissions.kick_members:
            return await ctx.respond(f"{emoji_no} Du brauchst die Berechtigung 'Mitglieder kicken'.", ephemeral=True)

        try:
            await member.kick(reason=reason)
            await ctx.respond(f"{emoji_yes} {member.mention} wurde gekickt.\nGrund: {reason}")
        except discord.Forbidden:
            await ctx.respond(f"{emoji_no} Ich kann dieses Mitglied nicht kicken.", ephemeral=True)

    # ✅ Timeout Command
    @commands.slash_command(name="timeout", description="Timeout für ein Mitglied")
    @option("member", discord.Member, description="Wen willst du muten?")
    @option("dauer", str, description="z. B. 10m, 1h, 1d", required=True)
    @option("reason", str, description="Grund für den Timeout", required=False)
    async def timeout(self, ctx: discord.ApplicationContext, member: discord.Member, dauer: str, reason: str = "Kein Grund angegeben"):
        if not ctx.author.guild_permissions.moderate_members:
            return await ctx.respond(f"{emoji_no} Du brauchst die Berechtigung 'Mitglieder moderieren'.", ephemeral=True)

        # Dauer parsen
        duration = self.parse_duration(dauer)
        if duration is None:
            return await ctx.respond(f"{emoji_no} Ungültige Dauer. Beispiel: `10m`, `1h`, `1d`", ephemeral=True)

        try:
            await member.timeout_for(duration, reason=reason)
            await ctx.respond(f"{emoji_yes} {emoji_user}{member.mention} wurde für {dauer} in Timeout versetzt.\nGrund: {reason}")
        except discord.Forbidden:
            await ctx.respond(f"{emoji_no} Ich kann dieses Mitglied nicht timeouten.", ephemeral=True)

    def parse_duration(self, dauer: str) -> timedelta | None:
        unit = dauer[-1]
        try:
            amount = int(dauer[:-1])
        except ValueError:
            return None

        if unit == "m":
            return timedelta(minutes=amount)
        elif unit == "h":
            return timedelta(hours=amount)
        elif unit == "d":
            return timedelta(days=amount)
        else:
            return None
def setup(bot):
    bot.add_cog(Moderation(bot))