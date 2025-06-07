import discord
from discord.ext import commands
from discord import slash_command, Option
import ezcord
import sqlite3
import datetime
import os

class WarnSystem(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Speicherort: cogs/moderation/Datenbanken/warns.db
        db_path = os.path.join(os.path.dirname(__file__), "Datenbanken", "warns.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    @slash_command(name="warn", description="Warn a user and save it to the database.")
    async def warn(
        self,
        ctx,
        user: Option(discord.Member, "User to warn"),
        reason: Option(str, "Reason for the warning")
    ):
        if not ctx.author.guild_permissions.kick_members:
            embed = discord.Embed(
                title="<:Xmark:1371016478979264512> × Fehler",
                color=discord.Color.red()
            )
            embed.add_field(name="<:Xmark:1371016478979264512> Du hast keine Berechtigung, Mitglieder zu verwarnen.", value="Bitte wende dich an einen Administrator.", inline=False)
            return await ctx.respond(embed=embed, ephemeral=True)

        timestamp = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M")
        self.cursor.execute(
            "INSERT INTO warns (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
            (ctx.guild.id, user.id, ctx.author.id, reason, timestamp)
        )
        self.conn.commit()
        warnings_embed = discord.Embed(
            title="Warnung",
            color=discord.Color.green()
        )
        warnings_embed.add_field(name="User", value=user.mention, inline=False)
        warnings_embed.add_field(name="Grund", value=reason, inline=False)
        warnings_embed.add_field(name="Verwarnt von", value=ctx.author.mention, inline=False)
        warnings_embed.add_field(name="Zeitstempel", value=timestamp, inline=False)
        warnings_embed.set_footer(text="Diese Warnung wurde in der Datenbank gespeichert.")

        await ctx.respond(f"⚠️ {user.mention} wurde verwarnt.\n**Grund:** {reason}", ephemeral=True)

    @slash_command(name="warnings", description="Zeigt die Verwarnungen eines Users an.")
    async def warnings(
        self,
        ctx,
        user: Option(discord.Member, "User whose warnings to show")
    ):
        self.cursor.execute(
            "SELECT id, reason, timestamp FROM warns WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, user.id)
        )
        results = self.cursor.fetchall()

        if not results:
            return await ctx.respond(f"{user.mention} hat keine Verwarnungen.", ephemeral=True)

        warn_list = "\n".join([f"ID `{warn_id}` | {timestamp} | Grund: {reason}" for warn_id, reason, timestamp in results])
        await ctx.respond(f"📋 Verwarnungen für {user.mention}:\n{warn_list}", ephemeral=True)

    @slash_command(name="unwarn", description="Löscht eine Verwarnung mit ID.")
    async def unwarn(
        self,
        ctx,
        warn_id: Option(int, "Die ID der Verwarnung")
    ):
        if not ctx.author.guild_permissions.kick_members:
            return await ctx.respond("❌ Du hast keine Berechtigung, Verwarnungen zu löschen.", ephemeral=True)

        self.cursor.execute("SELECT * FROM warns WHERE id = ?", (warn_id,))
        result = self.cursor.fetchone()

        if not result:
            return await ctx.respond("❌ Keine Verwarnung mit dieser ID gefunden.", ephemeral=True)

        self.cursor.execute("DELETE FROM warns WHERE id = ?", (warn_id,))
        self.conn.commit()
        await ctx.respond(f"✅ Verwarnung mit der ID `{warn_id}` wurde entfernt.", ephemeral=True)

def setup(bot):
    bot.add_cog(WarnSystem(bot))
