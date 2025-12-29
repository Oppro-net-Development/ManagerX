# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Imports
# ───────────────────────────────────────────────
import discord 
from discord import SlashCommandGroup
import datetime
import ezcord
from DevTools import NotesDatabase
from DevTools import emoji_no, emoji_yes
# ───────────────────────────────────────────────
# >> Cog
# ───────────────────────────────────────────────
class NotesCog(ezcord.Cog, group="moderation"):
    notes = SlashCommandGroup("notes", "📝 Verwaltung von Notizen für User")

    def __init__(self, bot):
        self.bot = bot
        self.db = NotesDatabase("data")

    @notes.command(name="add", description="📝 Speichere eine Notiz für einen User")
    async def add(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member,
        *,
        content: str
    ):
        if not content:
            return await ctx.respond("Bitte gib den Inhalt der Notiz an.", ephemeral=True)

        timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        self.db.add_note(ctx.guild.id, user.id, ctx.author.id, ctx.author.name, content, timestamp)
        await ctx.respond(f"Notiz für {user.mention} gespeichert.", ephemeral=True)

    @notes.command(name="list", description="📜 Zeige alle Notizen eines Users an")
    async def list(self, ctx: discord.ApplicationContext, user: discord.Member):
        notes = self.db.get_notes(ctx.guild.id, user.id)

        if not notes:
            return await ctx.respond(f"{emoji_no} {emoji_user}{user.mention} hat keine Notizen.", ephemeral=True)

        embed = discord.Embed(title=f"Notizen für {user.name}", color=discord.Color.blurple())
        for note in notes:
            embed.add_field(
                name=f"ID: {note['id']} – von {note['author_name']} am {note['timestamp']}",
                value=note['content'],
                inline=False
            )

        await ctx.respond(embed=embed, ephemeral=True)

    @notes.command(name="delete", description="🗑️ Lösche eine Notiz eines Users")
    async def delete(self, ctx: discord.ApplicationContext, user: discord.Member, note_id: int):
        notes = self.db.get_notes(ctx.guild.id, user.id)
        if not notes:
            return await ctx.respond(f"User {user} (ID: {user.id}) hat keine Notizen.", ephemeral=True)

        note_ids = [note['id'] for note in notes]
        if note_id not in note_ids:
            return await ctx.respond(f"{emoji_no} Notiz mit ID {note_id} existiert nicht für User {user}.", ephemeral=True)

        if self.db.delete_note(note_id):
            await ctx.respond(f"{emoji_yes} Notiz mit ID {note_id} von User {user} wurde gelöscht.", ephemeral=True)
        else:
            await ctx.respond(f"{emoji_no} Fehler beim Löschen der Notiz mit ID {note_id}.", ephemeral=True)


def setup(bot):
    bot.add_cog(NotesCog(bot))
