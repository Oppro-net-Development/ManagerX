# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────
from FastCoding.ui import emoji_no, emoji_yes, emoji_user, emoji_warning, emoji_circleinfo, emoji_addwarning
from FastCoding.ui import ERROR_TITLE, ERROR_COLOR, SUCCESS_COLOR, AUTHOR, FLOOTER
from FastCoding.backend import WarnDatabase
from FastCoding.backend import discord, slash_command, Option, datetime, os, ezcord
# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────
class WarnSystem(ezcord.Cog, group="moderation"):
    def __init__(self, bot):
        self.bot = bot
        base_path = os.path.dirname(__file__)
        self.db = WarnDatabase(base_path)

    @slash_command(name="warn", description="Warn a user and save it to the database.")
    async def warn(
            self,
            ctx,
            user: Option(discord.Member, "User to warn"),
            reason: Option(str, "Reason for the warning")
    ):
        if not ctx.author.guild_permissions.kick_members:
            embed = discord.Embed(
                title=ERROR_TITLE,
                color=ERROR_COLOR
            )
            embed.set_author(AUTHOR)
            embed.add_field(name=f"{emoji_no} Du hast keine Berechtigung, Mitglieder zu verwarnen.",
                            value="Bitte wende dich an einen Administrator.", inline=False)
            embed.set_footer(text=FLOOTER)
            return await ctx.respond(embed=embed, ephemeral=True)

        timestamp = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M")
        self.db.add_warning(ctx.guild.id, user.id, ctx.author.id, reason, timestamp)

        # Success embed for warning
        success_embed = discord.Embed(
            title=f"{emoji_warning} Warnung erteilt",
            color=SUCCESS_COLOR,
            description=f"{user.mention} wurde erfolgreich verwarnt."
        )
        success_embed.set_author(name=AUTHOR)
        success_embed.add_field(name=f"{emoji_user} Verwarnter User", value=user.mention, inline=True)
        success_embed.add_field(name=f"{emoji_user} Verwarnt von", value=ctx.author.mention, inline=True)
        success_embed.add_field(name=f"{emoji_circleinfo} Grund", value=reason, inline=False)
        success_embed.add_field(name=f"{emoji_circleinfo} Zeitstempel", value=timestamp, inline=False)
        success_embed.set_footer(text="Diese Warnung wurde in der Datenbank gespeichert.")

        await ctx.respond(embed=success_embed, ephemeral=True)

    @slash_command(name="warnings", description="Zeigt die Verwarnungen eines Users an.")
    async def warnings(
            self,
            ctx,
            user: Option(discord.Member, "User whose warnings to show")
    ):
        results = self.db.get_warnings(ctx.guild.id, user.id)

        if not results:
            # No warnings embed
            no_warnings_embed = discord.Embed(
                title=f"{emoji_circleinfo} Keine Verwarnungen",
                color=SUCCESS_COLOR,
                description=f"{user.mention} hat keine Verwarnungen."
            )
            no_warnings_embed.set_author(name=AUTHOR)
            no_warnings_embed.set_footer(text=FLOOTER)
            return await ctx.respond(embed=no_warnings_embed, ephemeral=True)

        # Warnings list embed
        warn_list = "\n".join(
            [f"**ID `{warn_id}`** | {timestamp}\n└ **Grund:** {reason}" for warn_id, reason, timestamp in results])

        warnings_embed = discord.Embed(
            title=f"{emoji_addwarning} Verwarnungen für {user.display_name}",
            color=ERROR_COLOR,
            description=warn_list
        )
        warnings_embed.set_author(name=AUTHOR)
        warnings_embed.add_field(name=f"{emoji_user} User", value=user.mention, inline=True)
        warnings_embed.add_field(name=f"{emoji_circleinfo} Anzahl Verwarnungen", value=str(len(results)), inline=True)
        warnings_embed.set_footer(text=FLOOTER)

        await ctx.respond(embed=warnings_embed, ephemeral=True)

    @slash_command(name="unwarn", description="Löscht eine Verwarnung mit ID.")
    async def unwarn(
            self,
            ctx,
            warn_id: Option(int, "Die ID der Verwarnung")
    ):
        if not ctx.author.guild_permissions.kick_members:
            # No permission embed
            no_perm_embed = discord.Embed(
                title=ERROR_TITLE,
                color=ERROR_COLOR
            )
            no_perm_embed.set_author(name=AUTHOR)
            no_perm_embed.add_field(name=f"{emoji_no} Keine Berechtigung",
                                    value="Du hast keine Berechtigung, Verwarnungen zu löschen.", inline=False)
            no_perm_embed.set_footer(text=FLOOTER)
            return await ctx.respond(embed=no_perm_embed, ephemeral=True)

        result = self.db.get_warning_by_id(warn_id)
        if not result:
            # Warning not found embed
            not_found_embed = discord.Embed(
                title=ERROR_TITLE,
                color=ERROR_COLOR
            )
            not_found_embed.set_author(name=AUTHOR)
            not_found_embed.add_field(name=f"{emoji_no} Verwarnung nicht gefunden",
                                      value=f"Keine Verwarnung mit der ID `{warn_id}` gefunden.", inline=False)
            not_found_embed.set_footer(text=FLOOTER)
            return await ctx.respond(embed=not_found_embed, ephemeral=True)

        self.db.delete_warning(warn_id)

        # Success removal embed
        removal_embed = discord.Embed(
            title=f"{emoji_yes} Verwarnung entfernt",
            color=SUCCESS_COLOR,
            description=f"Verwarnung mit der ID `{warn_id}` wurde erfolgreich entfernt."
        )
        removal_embed.set_author(name=AUTHOR)
        removal_embed.add_field(name=f"{emoji_user} Entfernt von", value=ctx.author.mention, inline=True)
        removal_embed.add_field(name=f"{emoji_circleinfo} Verwarnung ID", value=f"`{warn_id}`", inline=True)
        removal_embed.set_footer(text=FLOOTER)

        await ctx.respond(embed=removal_embed, ephemeral=True)


def setup(bot):
    bot.add_cog(WarnSystem(bot))