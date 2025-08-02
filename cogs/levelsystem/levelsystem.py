# Copyright (c) 2025 OPPRO.NET Network
import discord
from discord import SlashCommandGroup, Option
from discord.ext import commands
import time
import random
from FastCoding import LevelDatabase
import asyncio


class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = LevelDatabase()
        self.xp_cooldowns = {}  # User-ID -> Timestamp

    levelsystem = SlashCommandGroup("levelsystem", "Verwalte das Levelsystem")
    levelrole = SlashCommandGroup("levelrole", "Verwalte Level-Rollen")
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignoriere Bot-Nachrichten
        if message.author.bot:
            return

        # Nur in Servern, nicht in DMs
        if message.guild is None:
            return

        # Prüfe ob Levelsystem aktiviert ist
        if not self.db.is_levelsystem_enabled(message.guild.id):
            return

        user_id = message.author.id
        guild_id = message.guild.id
        current_time = time.time()

        # XP-Cooldown prüfen (60 Sekunden)
        if user_id in self.xp_cooldowns:
            if current_time - self.xp_cooldowns[user_id] < 30:
                return

        # XP hinzufügen (10-20 XP pro Nachricht)
        xp_gain = random.randint(10, 20)
        level_up, new_level = self.db.add_xp(user_id, guild_id, xp_gain)

        # Cooldown setzen
        self.xp_cooldowns[user_id] = current_time

        # Level Up Nachricht
        if level_up:
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} ist jetzt **Level {new_level}**!",
                color=0x00ff00
            )
            await message.channel.send(embed=embed)

            # Level-Rolle vergeben
            role_id = self.db.get_role_for_level(guild_id, new_level)
            if role_id:
                role = message.guild.get_role(role_id)
                if role:
                    try:
                        await message.author.add_roles(role)
                        embed = discord.Embed(
                            title="🏆 Neue Rolle!",
                            description=f"{message.author.mention} hat die Rolle **{role.name}** erhalten!",
                            color=0xffff00
                        )
                        await message.channel.send(embed=embed)
                    except discord.Forbidden:
                        pass

    @levelsystem.command(description="Zeigt das Server-Leaderboard")
    async def leaderboard(self, ctx,
                          anzahl: discord.Option(int, "Anzahl der User", default=10, min_value=1, max_value=25)):
        if not self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="❌ Levelsystem deaktiviert",
                description="Das Levelsystem ist auf diesem Server deaktiviert.",
                color=0xff0000
            )
            await ctx.respond(embed=embed)
            return

        leaderboard_data = self.db.get_leaderboard(ctx.guild.id, anzahl)

        if not leaderboard_data:
            embed = discord.Embed(
                title="📊 Leaderboard",
                description="Noch keine User im Leaderboard!",
                color=0x0099ff
            )
            await ctx.respond(embed=embed)
            return

        embed = discord.Embed(
            title=f"📊 Leaderboard - Top {len(leaderboard_data)}",
            color=0x0099ff
        )

        description = ""
        for i, (user_id, xp, level, messages) in enumerate(leaderboard_data, 1):
            user = self.bot.get_user(user_id)
            username = user.display_name if user else f"User {user_id}"

            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"**{i}.**"

            description += f"{medal} **{username}** - Level {level} ({xp:,} XP)\n"

        embed.description = description
        embed.set_footer(text=f"Server: {ctx.guild.name}")

        await ctx.respond(embed=embed)

    @levelsystem.command(description="Zeigt dein Profil oder das eines anderen Users")
    async def profil(self, ctx,
                     user: discord.Option(discord.Member, "User dessen Profil angezeigt werden soll", default=None)):
        if not self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="❌ Levelsystem deaktiviert",
                description="Das Levelsystem ist auf diesem Server deaktiviert.",
                color=0xff0000
            )
            await ctx.respond(embed=embed)
            return

        target_user = user or ctx.author
        user_stats = self.db.get_user_stats(target_user.id, ctx.guild.id)

        if not user_stats:
            embed = discord.Embed(
                title="❌ Kein Profil gefunden",
                description=f"{target_user.display_name} hat noch keine XP gesammelt!",
                color=0xff0000
            )
            await ctx.respond(embed=embed)
            return

        xp, level, messages, xp_needed = user_stats
        rank = self.db.get_user_rank(target_user.id, ctx.guild.id)

        embed = discord.Embed(
            title=f"📊 Profil von {target_user.display_name}",
            color=target_user.color or 0x0099ff
        )

        embed.add_field(name="🏆 Level", value=str(level), inline=True)
        embed.add_field(name="⭐ XP", value=f"{xp:,}", inline=True)
        embed.add_field(name="📈 Rang", value=f"#{rank}", inline=True)
        embed.add_field(name="💬 Nachrichten", value=str(messages), inline=True)
        embed.add_field(name="🎯 XP bis nächstes Level", value=f"{xp_needed:,}", inline=True)

        # Fortschrittsbalken
        current_level_xp = xp - self.db.xp_for_level(level)
        next_level_xp = self.db.xp_for_level(level + 1) - self.db.xp_for_level(level)
        progress = current_level_xp / next_level_xp if next_level_xp > 0 else 1

        progress_bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
        embed.add_field(name="📊 Fortschritt", value=f"`{progress_bar}` {progress * 100:.1f}%", inline=False)

        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
        embed.set_footer(text=f"Server: {ctx.guild.name}")

        await ctx.respond(embed=embed)

    @levelrole.command(description="Fügt eine Level-Rolle hinzu")
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx, level: discord.Option(int, "Level für die Rolle", min_value=1),
                  rolle: discord.Option(discord.Role, "Die Rolle die vergeben werden soll")):
        if rolle.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Keine Berechtigung",
                description="Du kannst keine Rolle hinzufügen, die höher oder gleich deiner höchsten Rolle ist!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if rolle.position >= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title="❌ Bot-Berechtigung fehlt",
                description="Ich kann diese Rolle nicht vergeben, da sie höher oder gleich meiner höchsten Rolle ist!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.add_level_role(ctx.guild.id, level, rolle.id)

        embed = discord.Embed(
            title="✅ Level-Rolle hinzugefügt",
            description=f"Die Rolle **{rolle.name}** wird nun bei **Level {level}** vergeben!",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelrole.command(description="Bearbeitet eine bestehende Level-Rolle")
    @commands.has_permissions(manage_roles=True)
    async def edit(self, ctx, level: discord.Option(int, "Level der zu bearbeitenden Rolle", min_value=1),
                   neue_rolle: discord.Option(discord.Role, "Die neue Rolle")):
        # Prüfen ob Level-Rolle existiert
        level_roles = self.db.get_level_roles(ctx.guild.id)
        if not any(l == level for l, r in level_roles):
            embed = discord.Embed(
                title="❌ Level-Rolle nicht gefunden",
                description=f"Für Level {level} ist keine Rolle konfiguriert!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if neue_rolle.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Keine Berechtigung",
                description="Du kannst keine Rolle setzen, die höher oder gleich deiner höchsten Rolle ist!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        if neue_rolle.position >= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title="❌ Bot-Berechtigung fehlt",
                description="Ich kann diese Rolle nicht vergeben, da sie höher oder gleich meiner höchsten Rolle ist!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.add_level_role(ctx.guild.id, level, neue_rolle.id)

        embed = discord.Embed(
            title="✅ Level-Rolle bearbeitet",
            description=f"Die Rolle für **Level {level}** wurde zu **{neue_rolle.name}** geändert!",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelrole.command(description="Entfernt eine Level-Rolle")
    @commands.has_permissions(manage_roles=True)
    async def remove(self, ctx, level: discord.Option(int, "Level der zu entfernenden Rolle", min_value=1)):
        # Prüfen ob Level-Rolle existiert
        level_roles = self.db.get_level_roles(ctx.guild.id)
        if not any(l == level for l, r in level_roles):
            embed = discord.Embed(
                title="❌ Level-Rolle nicht gefunden",
                description=f"Für Level {level} ist keine Rolle konfiguriert!",
                color=0xff0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.remove_level_role(ctx.guild.id, level)

        embed = discord.Embed(
            title="✅ Level-Rolle entfernt",
            description=f"Die Level-Rolle für **Level {level}** wurde entfernt!",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelrole.command(description="Zeigt alle konfigurierten Level-Rollen")
    async def list(self, ctx):
        level_roles = self.db.get_level_roles(ctx.guild.id)

        if not level_roles:
            embed = discord.Embed(
                title="📝 Level-Rollen",
                description="Keine Level-Rollen konfiguriert!",
                color=0x0099ff
            )
            await ctx.respond(embed=embed)
            return

        embed = discord.Embed(
            title="📝 Level-Rollen",
            color=0x0099ff
        )

        description = ""
        for level, role_id in level_roles:
            role = ctx.guild.get_role(role_id)
            role_name = role.name if role else f"Gelöschte Rolle ({role_id})"
            description += f"**Level {level}:** {role_name}\n"

        embed.description = description
        embed.set_footer(text=f"Server: {ctx.guild.name}")

        await ctx.respond(embed=embed)


    @levelsystem.command(description="Aktiviert das Levelsystem")
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx):
        if self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="ℹ️ Bereits aktiviert",
                description="Das Levelsystem ist bereits aktiviert!",
                color=0x0099ff
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.set_levelsystem_enabled(ctx.guild.id, True)

        embed = discord.Embed(
            title="✅ Levelsystem aktiviert",
            description="Das Levelsystem wurde erfolgreich aktiviert!",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelsystem.command(description="Deaktiviert das Levelsystem")
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx):
        if not self.db.is_levelsystem_enabled(ctx.guild.id):
            embed = discord.Embed(
                title="ℹ️ Bereits deaktiviert",
                description="Das Levelsystem ist bereits deaktiviert!",
                color=0x0099ff
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        self.db.set_levelsystem_enabled(ctx.guild.id, False)

        embed = discord.Embed(
            title="✅ Levelsystem deaktiviert",
            description="Das Levelsystem wurde erfolgreich deaktiviert!",
            color=0x00ff00
        )
        await ctx.respond(embed=embed)

    @levelsystem.command(description="Zeigt den Status des Levelsystems")
    async def status(self, ctx):
        enabled = self.db.is_levelsystem_enabled(ctx.guild.id)

        embed = discord.Embed(
            title="📊 Levelsystem Status",
            description=f"Das Levelsystem ist **{'aktiviert' if enabled else 'deaktiviert'}**",
            color=0x00ff00 if enabled else 0xff0000
        )

        # Zusätzliche Statistiken
        if enabled:
            leaderboard = self.db.get_leaderboard(ctx.guild.id, 1)
            level_roles = self.db.get_level_roles(ctx.guild.id)

            embed.add_field(name="👥 Aktive User", value=str(len(self.db.get_leaderboard(ctx.guild.id, 1000))),
                            inline=True)
            embed.add_field(name="🏆 Level-Rollen", value=str(len(level_roles)), inline=True)

            if leaderboard:
                top_user = self.bot.get_user(leaderboard[0][0])
                top_username = top_user.display_name if top_user else f"User {leaderboard[0][0]}"
                embed.add_field(name="👑 Top User", value=f"{top_username} (Level {leaderboard[0][2]})", inline=True)

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(LevelSystem(bot))