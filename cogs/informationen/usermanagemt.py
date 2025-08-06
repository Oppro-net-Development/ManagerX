import discord
from discord import slash_command, Option, SlashCommandGroup

import ezcord

class UserManagement(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    user = SlashCommandGroup("user", "Benutzerverwaltung")

    @user.command(description="Zeigt Informationen über einen Benutzer an")
    async def info(self, ctx, user: Option(discord.User, "Der Benutzer, über den du Informationen erhalten möchtest")):
        embed = discord.Embed(
            title=f"Informationen über {user.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Benutzername", value=user.name, inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name="Erstellt am", value=user.created_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="Status", value=str(user.status).capitalize(), inline=True)
        embed.add_field(name="Bot", value="Ja" if user.bot else "Nein", inline=True)
        embed.add_field(name="Gemeinsam im Server", value=f"{len(user.mutual_guilds)} Server", inline=True)
        embed.add_field(name="Avatar URL", value=user.avatar.url if user.avatar else "Kein Avatar", inline=True)
        embed.set_footer(text=f"Angefordert von {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        else:
            embed.set_thumbnail(url=user.default_avatar.url)
        await ctx.respond(embed=embed)

    @user.command(description="Zeigt die Rollen eines Benutzers an")
    async def roles(self, ctx, user: Option(discord.User, "Der Benutzer, dessen Rollen du sehen möchtest")):
        roles = user.roles[1:]  # [1:] to skip the @everyone role
        if not roles:
            await ctx.respond(f"{user.name} hat keine Rollen.")
            return
        embed = discord.Embed(
            title=f"Rollen von {user.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Rollen", value=", ".join(role.name for role in roles), inline=False)
        embed.set_footer(text=f"Angefordert von {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.respond(embed=embed)

    @user.command(description="Setzt den Nicknamen eines Benutzers")
    @discord.default_permissions(manage_member=True)
    async def set_nickname(self, ctx, user: Option(discord.Member, "Der Benutzer, dessen Nicknamen du ändern möchtest"), nickname: Option(str, "Der neue Nickname")):
        if not nickname:
            await ctx.respond("Bitte gib einen gültigen Nicknamen an.")
            return
        await user.edit(nick=nickname)
        await ctx.respond(f"Der Nickname von {user.name} wurde auf '{nickname}' geändert.")

        
    @user.command(description="Entfernt alle Rollen eines Benutzers")
    @discord.default_permissions(manage_roles=True)
    async def remove_roles(self, ctx, user: Option(discord.Member, "Der Benutzer, dessen Rollen du entfernen möchtest")):
        roles = user.roles[1:]  # [1:] to skip the @everyone role
        if not roles:
            await ctx.respond(f"{user.name} hat keine Rollen, die entfernt werden können.")
            return
        await user.remove_roles(*roles)
        await ctx.respond(f"Alle Rollen von {user.name} wurden entfernt.")


    @user.command(description="Gibt einem Benutzer eine Rolle")
    @discord.default_permissions(manage_roles=True)
    async def give_role(self, ctx, user: Option(discord.Member, "Der Benutzer, dem du eine Rolle geben möchtest"), role: Option(discord.Role, "Die Rolle, die du vergeben möchtest")):
        if role in user.roles:
            await ctx.respond(f"{user.name} hat bereits die Rolle {role.name}.")
            return
        await user.add_roles(role)
        await ctx.respond(f"Die Rolle {role.name} wurde {user.name} zugewiesen.")


    @user.command(description="Entfernt eine Rolle von einem Benutzer")
    @discord.default_permissions(manage_roles=True)
    async def remove_role(self, ctx, user: Option(discord.Member, "Der Benutzer, von dem du eine Rolle entfernen möchtest"), role: Option(discord.Role, "Die Rolle, die du entfernen möchtest")):
        if role not in user.roles:
            await ctx.respond(f"{user.name} hat die Rolle {role.name} nicht.")
            return
        await user.remove_roles(role)
        await ctx.respond(f"Die Rolle {role.name} wurde von {user.name} entfernt.")
def setup(bot):
    bot.add_cog(UserManagement(bot))
