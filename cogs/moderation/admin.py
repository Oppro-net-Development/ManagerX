# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────

from FastCoding.backend import discord, ezcord, slash_command, option, timedelta

from FastCoding.backend import KICK, BAN, MODERATE
from FastCoding.ui import emoji_yes, emoji_no, emoji_user, ERROR_TITLE, ERROR_COLOR
# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────
class moderation(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ✅ Ban Command
    @slash_command(name="ban", description="Bannt ein Mitglied")
    @option("member", discord.Member, description="Wen willst du bannen?")
    @option("reason", str, description="Grund für den Bann", required=False)
    async def ban(self, ctx: discord.ApplicationContext, member: discord.Member, reason: str = "Kein Grund angegeben"):
        if not getattr(ctx.author.guild_permissions, BAN):
            notpr_embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Du hast nicht die Berechtigung, Mitglieder zu bannen.",
                color=ERROR_COLOR
            )
            return await ctx.respond(embed=notpr_embed, ephemeral=True)

        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title=f"{emoji_yes} × Bann erfolgreich",
                description=f"{emoji_user}{member.mention} wurde gebannt.",
                color=discord.Color.red()
            )
            embed.add_field(name="Grund", value=reason, inline=False)
            await ctx.respond(embed=embed, ephemeral=True)
        except discord.Forbidden:
            error_embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Ich habe nicht die Berechtigung, dieses Mitglied zu bannen.",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=error_embed, ephemeral=True)

    # ✅ Kick Command
    @slash_command(name="kick", description="Kickt ein Mitglied")
    @option("member", discord.Member, description="Wen willst du kicken?")
    @option("reason", str, description="Grund für den Kick", required=False)
    async def kick(self, ctx: discord.ApplicationContext, member: discord.Member, reason: str = "Kein Grund angegeben"):
        if not getattr(ctx.author.guild_permissions, KICK):
            notpr_embed = discord.Embed(
                title=ERROR_TITLE,
                description= f"{emoji_no} Du hast nicht die Berechtigung, Mitglieder zu kicken.",
                color=ERROR_COLOR
            )
            return await ctx.respond(embed=notpr_embed, ephemeral=True)

        try:
            await member.kick(reason=reason)
            kick_embed = discord.Embed(
                title=f"{emoji_yes} × Kick erfolgreich",
                description=f"{emoji_user}{member.mention} wurde gekickt.",
                color=discord.Color.red()
            )
            kick_embed.add_field(name="Grund", value=reason, inline=False)
            await ctx.respond(embed=kick_embed, ephemeral=True)
        except discord.Forbidden:
            error_embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Ich habe nicht die Berechtigung, dieses Mitglied zu kicken.",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=error_embed, ephemeral=True)

    # ✅ Timeout Command
    @slash_command(name="timeout", description="Timeout für ein Mitglied")
    @option("member", discord.Member, description="Wen willst du muten?")
    @option("dauer", str, description="z. B. 10m, 1h, 1d", required=True)
    @option("reason", str, description="Grund für den Timeout", required=False)
    async def timeout(self, ctx: discord.ApplicationContext, member: discord.Member, dauer: str, reason: str = "Kein Grund angegeben"):
        if not getattr(ctx.author.guild_permissions, MODERATE):
            notpr_embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Du hast nicht die Berechtigung, Mitglieder zu muten.",
                color=ERROR_COLOR
            )
            return await ctx.respond(embed=notpr_embed, ephemeral=True)

        # Dauer parsen
        duration = self.parse_duration(dauer)
        if duration is None:
            error_embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Ungültige Dauer. Beispiel: `10m`, `1h`, `1d`",
                color=ERROR_COLOR
            )
            return await ctx.respond(embed=error_embed, ephemeral=True)

        try:
            await member.timeout_for(duration, reason=reason)
            embed = discord.Embed(
                title=f"{emoji_yes} × Timeout erfolgreich",
                description=f"{emoji_user}{member.mention} wurde für {dauer} in Timeout versetzt.",
                color=discord.Color.red()
            )
            embed.add_field(name="Grund", value=reason, inline=False)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            error_embed = discord.Embed(
                title=ERROR_TITLE,
                description=f"{emoji_no} Ich habe nicht die Berechtigung, dieses Mitglied zu timeouten.",
                color=ERROR_COLOR
            )
            await ctx.respond(embed=error_embed, ephemeral=True)

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
    bot.add_cog(moderation(bot))
