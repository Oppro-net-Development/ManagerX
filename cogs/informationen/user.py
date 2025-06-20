# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────
from FastCoding.backend import discord, slash_command, ezcord, Option
# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────

class UserInfo(ezcord.Cog, group="Infomation"):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        description="Zeigt Informationen über den Benutzer an."
    )
    async def userinfo(
        self,
        ctx,
        user: Option(discord.User, "Der Benutzer, dessen Informationen angezeigt werden sollen", required=False)
    ):
        if user is None:
            user = ctx.author

        embed = discord.Embed(
            title=f"Benutzerinfo für {user.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="🆔Benutzer-ID", value=user.id, inline=False)
        embed.add_field(name="📅Erstellt am", value=user.created_at.strftime("%d.%m.%Y"), inline=False)
        embed.add_field(name="📅Beigetreten am", value=user.joined_at.strftime("%d.%m.%Y") if user.joined_at else "Unbekannt", inline=False)
        embed.add_field(name="🛼Rollen", value=", ".join([role.name for role in user.roles[1:]]) if len(user.roles) > 1 else "Keine Rollen", inline=False)
        await ctx.send(embed=embed)
def setup(bot):
    bot.add_cog(UserInfo(bot))