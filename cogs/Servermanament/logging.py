import discord
from discord.ext import commands
from datetime import datetime
from FastCoding import LoggingDatabase


class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = LoggingDatabase()

    async def send_log(self, guild_id: int, embed: discord.Embed):
        """Sendet ein Log-Embed in den konfigurierten Channel"""
        channel_id = await self.db.get_log_channel(guild_id)
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if channel:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                print(f"Keine Berechtigung für Log-Channel in Guild {guild_id}")
            except Exception as e:
                print(f"Fehler beim Senden des Logs: {e}")

    # Slash Commands für Setup

    @discord.slash_command(name="setlogchannel", description="Setzt den Log-Channel")
    @discord.default_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        await self.db.set_log_channel(ctx.guild.id, channel.id)

        embed = discord.Embed(
            title="✅ Log-Channel gesetzt",
            description=f"Logs werden nun in {channel.mention} gesendet.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        await ctx.respond(embed=embed)

    @discord.slash_command(name="removelogchannel", description="Entfernt den Log-Channel")
    @discord.default_permissions(administrator=True)
    async def remove_log_channel(self, ctx):
        await self.db.remove_log_channel(ctx.guild.id)

        embed = discord.Embed(
            title="🗑️ Log-Channel entfernt",
            description="Logging wurde für diesen Server deaktiviert.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        await ctx.respond(embed=embed)

    # Event Listeners

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Member beitritt"""
        embed = discord.Embed(
            title="📥 Member beigetreten",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{member.mention} ({member})", inline=False)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Erstellt am", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)

        await self.send_log(member.guild.id, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Member verlässt Server"""
        embed = discord.Embed(
            title="📤 Member verlassen",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Beigetreten am",
                        value=f"<t:{int(member.joined_at.timestamp())}:F>" if member.joined_at else "Unbekannt",
                        inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)

        await self.send_log(member.guild.id, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Member wurde gebannt"""
        embed = discord.Embed(
            title="🔨 Member gebannt",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)

        # Versuche Ban-Info zu holen
        try:
            ban_info = await guild.fetch_ban(user)
            if ban_info.reason:
                embed.add_field(name="Grund", value=ban_info.reason, inline=False)
        except:
            pass

        await self.send_log(guild.id, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Member wurde entbannt"""
        embed = discord.Embed(
            title="🔓 Member entbannt",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)

        await self.send_log(guild.id, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Nachricht gelöscht"""
        if message.author.bot or not message.guild:
            return

        embed = discord.Embed(
            title="🗑️ Nachricht gelöscht",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Author", value=f"{message.author.mention} ({message.author})", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Message ID", value=message.id, inline=True)

        if message.content:
            content = message.content[:1024] if len(message.content) > 1024 else message.content
            embed.add_field(name="Inhalt", value=content, inline=False)

        if message.attachments:
            attach_list = "\n".join([att.filename for att in message.attachments[:5]])
            embed.add_field(name="Anhänge", value=attach_list, inline=False)

        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)

        await self.send_log(message.guild.id, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Nachricht bearbeitet"""
        if before.author.bot or not before.guild or before.content == after.content:
            return

        embed = discord.Embed(
            title="✏️ Nachricht bearbeitet",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Author", value=f"{before.author.mention} ({before.author})", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Zur Nachricht", value=f"[Klick hier]({after.jump_url})", inline=True)

        if before.content:
            old_content = before.content[:512] if len(before.content) > 512 else before.content
            embed.add_field(name="Vorher", value=old_content, inline=False)

        if after.content:
            new_content = after.content[:512] if len(after.content) > 512 else after.content
            embed.add_field(name="Nachher", value=new_content, inline=False)

        embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)

        await self.send_log(before.guild.id, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Channel erstellt"""
        embed = discord.Embed(
            title="📁 Channel erstellt",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Channel", value=f"{channel.mention} ({channel.name})", inline=False)
        embed.add_field(name="Typ", value=str(channel.type).title(), inline=True)
        embed.add_field(name="ID", value=channel.id, inline=True)

        await self.send_log(channel.guild.id, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Channel gelöscht"""
        embed = discord.Embed(
            title="🗑️ Channel gelöscht",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Channel", value=f"#{channel.name}", inline=False)
        embed.add_field(name="Typ", value=str(channel.type).title(), inline=True)
        embed.add_field(name="ID", value=channel.id, inline=True)

        await self.send_log(channel.guild.id, embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Rolle erstellt"""
        embed = discord.Embed(
            title="🎭 Rolle erstellt",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Rolle", value=f"{role.mention} ({role.name})", inline=False)
        embed.add_field(name="Farbe", value=str(role.color), inline=True)
        embed.add_field(name="ID", value=role.id, inline=True)

        await self.send_log(role.guild.id, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Rolle gelöscht"""
        embed = discord.Embed(
            title="🗑️ Rolle gelöscht",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Rolle", value=role.name, inline=False)
        embed.add_field(name="Farbe", value=str(role.color), inline=True)
        embed.add_field(name="ID", value=role.id, inline=True)

        await self.send_log(role.guild.id, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Member Update (Nickname, Rollen)"""
        if before.nick != after.nick:
            embed = discord.Embed(
                title="📝 Nickname geändert",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{after.mention} ({after})", inline=False)
            embed.add_field(name="Vorher", value=before.nick or before.name, inline=True)
            embed.add_field(name="Nachher", value=after.nick or after.name, inline=True)
            embed.set_thumbnail(url=after.display_avatar.url)

            await self.send_log(after.guild.id, embed)

        # Rollen-Änderungen
        if before.roles != after.roles:
            added_roles = set(after.roles) - set(before.roles)
            removed_roles = set(before.roles) - set(after.roles)

            if added_roles:
                embed = discord.Embed(
                    title="➕ Rolle hinzugefügt",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="User", value=f"{after.mention} ({after})", inline=False)
                embed.add_field(name="Rollen", value=", ".join([role.mention for role in added_roles]), inline=False)
                embed.set_thumbnail(url=after.display_avatar.url)

                await self.send_log(after.guild.id, embed)

            if removed_roles:
                embed = discord.Embed(
                    title="➖ Rolle entfernt",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="User", value=f"{after.mention} ({after})", inline=False)
                embed.add_field(name="Rollen", value=", ".join([role.name for role in removed_roles]), inline=False)
                embed.set_thumbnail(url=after.display_avatar.url)

                await self.send_log(after.guild.id, embed)


def setup(bot):
    bot.add_cog(LoggingCog(bot))