from FastCoding import AutoDeleteDB
import discord
from discord.ext import tasks
from discord.commands import SlashCommandGroup, Option
import ezcord

class AutoDelete(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delete_task.start()

    autodelete = SlashCommandGroup("autodelete", "Automatische Nachrichtenlöschung")

    # Setup-Befehl
    @autodelete.command(name="setup", description="Richtet AutoDelete für einen Kanal ein.")
    async def setup(self, ctx,
                    channel: Option(discord.TextChannel, "Kanal", required=True),
                    duration: Option(int, "Zeit in Sekunden", required=True)):
        AutoDeleteDB().add_autodelete(channel.id, duration)
        await ctx.respond(f"✅ AutoDelete für {channel.mention} wurde mit {duration} Sekunden aktiviert.", ephemeral=True)

    # List-Befehl
    @autodelete.command(name="list", description="Zeigt alle aktiven AutoDelete-Kanäle.")
    async def list(self, ctx):
        db = AutoDeleteDB()
        channels = db.get_all()  # Du musst get_all in deiner DB-Klasse definieren!
        if not channels:
            await ctx.respond("❌ Keine AutoDelete-Kanäle gefunden.", ephemeral=True)
            return

        message = "**Aktive AutoDelete-Kanäle:**\n"
        for chan_id, duration in channels:
            channel = self.bot.get_channel(chan_id)
            if channel:
                message += f"• {channel.mention} – {duration}s\n"
            else:
                message += f"• Unbekannter Kanal ({chan_id}) – {duration}s\n"
        await ctx.respond(message, ephemeral=True)

    # Entfernen
    @autodelete.command(name="remove", description="Entfernt AutoDelete von einem Kanal.")
    async def remove(self, ctx,
                     channel: Option(discord.TextChannel, "Kanal", required=True)):
        AutoDeleteDB().remove_autodelete(channel.id)
        await ctx.respond(f"🗑️ AutoDelete für {channel.mention} wurde entfernt.", ephemeral=True)

    # Hintergrund-Task zum Löschen
    @tasks.loop(seconds=10)
    async def delete_task(self):
        db = AutoDeleteDB()
        channels = db.get_all()
        for chan_id, duration in channels:
            channel = self.bot.get_channel(chan_id)
            if channel:
                try:
                    async for msg in channel.history(limit=100):
                        if (discord.utils.utcnow() - msg.created_at).total_seconds() >= duration:
                            await msg.delete()
                except Exception as e:
                    print(f"[Fehler beim Löschen in {chan_id}]: {e}")

    @delete_task.before_loop
    async def before_delete_task(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(AutoDelete(bot))
