import discord
from discord.ext import commands
from FastCoding import WelcomeDatabase  # Angepasster Import
import re
from typing import Optional
import asyncio

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = WelcomeDatabase()
    
    def replace_placeholders(self, text: str, member: discord.Member, guild: discord.Guild) -> str:
        """Ersetzt Placeholder in der Welcome Message"""
        if not text:
            return text
        
        placeholders = {
            '%user%': member.display_name,
            '%username%': member.name,
            '%mention%': member.mention,
            '%tag%': str(member),
            '%userid%': str(member.id),
            '%servername%': guild.name,
            '%serverid%': str(guild.id),
            '%membercount%': str(guild.member_count),
            '%joindate%': member.joined_at.strftime('%d.%m.%Y') if member.joined_at else 'Unbekannt',
            '%createddate%': member.created_at.strftime('%d.%m.%Y'),
            '%server%': guild.name,  # Alternative zu servername
            '%guild%': guild.name,   # Alternative zu servername
        }
        
        # Placeholder ersetzen
        for placeholder, value in placeholders.items():
            text = text.replace(placeholder, str(value))
        
        return text
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Event wird ausgelöst, wenn ein neuer User dem Server beitritt"""
        try:
            settings = await self.db.get_welcome_settings(member.guild.id)
            
            if not settings or not settings.get('enabled', True):
                return
            
            channel_id = settings.get('channel_id')
            if not channel_id:
                return
            
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return
            
            welcome_message = settings.get('welcome_message', 'Willkommen %mention% auf **%servername%**! 🎉')
            
            # Placeholder ersetzen
            processed_message = self.replace_placeholders(welcome_message, member, member.guild)
            
            # Embed oder normale Nachricht senden
            if settings.get('embed_enabled', False):
                embed = discord.Embed()
                
                # Embed Farbe
                color_hex = settings.get('embed_color', '#00ff00')
                try:
                    color = int(color_hex.replace('#', ''), 16)
                    embed.color = discord.Color(color)
                except:
                    embed.color = discord.Color.green()
                
                # Embed Titel
                embed_title = settings.get('embed_title')
                if embed_title:
                    embed.title = self.replace_placeholders(embed_title, member, member.guild)
                
                # Embed Beschreibung
                embed_description = settings.get('embed_description')
                if embed_description:
                    embed.description = self.replace_placeholders(embed_description, member, member.guild)
                else:
                    embed.description = processed_message
                
                # Embed Thumbnail (User Avatar)
                if settings.get('embed_thumbnail', False):
                    embed.set_thumbnail(url=member.display_avatar.url)
                
                # Embed Footer
                embed_footer = settings.get('embed_footer')
                if embed_footer:
                    embed.set_footer(text=self.replace_placeholders(embed_footer, member, member.guild))
                
                # Nachricht senden
                if settings.get('ping_user', False):
                    content = member.mention
                else:
                    content = None
                
                msg = await channel.send(content=content, embed=embed)
            else:
                msg = await channel.send(processed_message)
            
            # Auto-Delete nach bestimmter Zeit
            delete_after = settings.get('delete_after', 0)
            if delete_after > 0:
                await asyncio.sleep(delete_after)
                try:
                    await msg.delete()
                except:
                    pass
                    
        except Exception as e:
            print(f"Fehler im Welcome System: {e}")
    
    welcome = discord.SlashCommandGroup("welcome", "Welcome System Einstellungen")
    
    @welcome.command(name="channel", description="Setzt den Welcome Channel")
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(self, ctx, channel: discord.TextChannel):
        """Setzt den Channel für Welcome Messages"""
        success = await self.db.update_welcome_settings(ctx.guild.id, channel_id=channel.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Welcome Channel gesetzt",
                description=f"Welcome Messages werden nun in {channel.mention} gesendet.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Fehler",
                description="Der Welcome Channel konnte nicht gesetzt werden.",
                color=discord.Color.red()
            )
        
        await ctx.respond(embed=embed)
    
    @welcome.command(name="message", description="Setzt die Welcome Message")
    @commands.has_permissions(administrator=True)
    async def set_welcome_message(self, ctx, *, message: str):
        """Setzt die Welcome Message"""
        success = await self.db.update_welcome_settings(ctx.guild.id, welcome_message=message)
        
        if success:
            embed = discord.Embed(
                title="✅ Welcome Message gesetzt",
                description=f"**Neue Message:**\n{message}",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📝 Verfügbare Placeholder",
                value=(
                    "`%user%` - Username\n"
                    "`%mention%` - User erwähnen\n"
                    "`%servername%` - Servername\n"
                    "`%membercount%` - Mitgliederanzahl\n"
                    "`%joindate%` - Beitrittsdatum\n"
                    "Und weitere..."
                ),
                inline=False
            )
        else:
            embed = discord.Embed(
                title="❌ Fehler",
                description="Die Welcome Message konnte nicht gesetzt werden.",
                color=discord.Color.red()
            )
        
        await ctx.respond(embed=embed)
    
    @welcome.command(name="toggle", description="Schaltet das Welcome System ein/aus")
    @commands.has_permissions(administrator=True)
    async def toggle_welcome(self, ctx):
        """Schaltet das Welcome System ein oder aus"""
        new_state = await self.db.toggle_welcome(ctx.guild.id)
        
        if new_state is None:
            embed = discord.Embed(
                title="❌ Fehler",
                description="Es sind noch keine Welcome Einstellungen vorhanden. Setze zuerst einen Channel.",
                color=discord.Color.red()
            )
        else:
            status = "aktiviert" if new_state else "deaktiviert"
            embed = discord.Embed(
                title=f"✅ Welcome System {status}",
                description=f"Das Welcome System wurde **{status}**.",
                color=discord.Color.green() if new_state else discord.Color.orange()
            )
        
        await ctx.respond(embed=embed)
    
    @welcome.command(name="embed", description="Aktiviert/Deaktiviert Embed Modus")
    @commands.has_permissions(administrator=True)
    async def toggle_embed(self, ctx, enabled: bool):
        """Aktiviert oder deaktiviert Embed Welcome Messages"""
        success = await self.db.update_welcome_settings(ctx.guild.id, embed_enabled=enabled)
        
        if success:
            status = "aktiviert" if enabled else "deaktiviert"
            embed = discord.Embed(
                title=f"✅ Embed Modus {status}",
                description=f"Welcome Messages werden nun {'als Embed' if enabled else 'als normale Nachricht'} gesendet.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Fehler",
                description="Der Embed Modus konnte nicht geändert werden.",
                color=discord.Color.red()
            )
        
        await ctx.respond(embed=embed)
    
    @welcome.command(name="config", description="Zeigt die aktuelle Konfiguration")
    @commands.has_permissions(administrator=True)
    async def show_config(self, ctx):
        """Zeigt die aktuelle Welcome Konfiguration"""
        settings = await self.db.get_welcome_settings(ctx.guild.id)
        
        if not settings:
            embed = discord.Embed(
                title="❌ Keine Konfiguration gefunden",
                description="Es sind noch keine Welcome Einstellungen vorhanden.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed)
            return
        
        channel = self.bot.get_channel(settings.get('channel_id')) if settings.get('channel_id') else None
        
        embed = discord.Embed(
            title="⚙️ Welcome System Konfiguration",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Status",
            value="✅ Aktiviert" if settings.get('enabled') else "❌ Deaktiviert",
            inline=True
        )
        
        embed.add_field(
            name="Channel",
            value=channel.mention if channel else "❌ Nicht gesetzt",
            inline=True
        )
        
        embed.add_field(
            name="Embed Modus",
            value="✅ Aktiviert" if settings.get('embed_enabled') else "❌ Deaktiviert",
            inline=True
        )
        
        message = settings.get('welcome_message', 'Nicht gesetzt')
        if len(message) > 100:
            message = message[:100] + "..."
        
        embed.add_field(
            name="Welcome Message",
            value=f"```{message}```",
            inline=False
        )
        
        await ctx.respond(embed=embed)
    
    @welcome.command(name="test", description="Testet die Welcome Message")
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx):
        """Testet die Welcome Message mit dem aktuellen User"""
        settings = await self.db.get_welcome_settings(ctx.guild.id)
        
        if not settings or not settings.get('channel_id'):
            embed = discord.Embed(
                title="❌ Fehler",
                description="Es ist kein Welcome Channel gesetzt.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        # Simuliere Member Join Event
        member = ctx.author
        welcome_message = settings.get('welcome_message', 'Willkommen %mention% auf **%servername%**! 🎉')
        processed_message = self.replace_placeholders(welcome_message, member, ctx.guild)
        
        embed = discord.Embed(
            title="🧪 Welcome Message Test",
            description=f"**Vorschau:**\n{processed_message}",
            color=discord.Color.blue()
        )
        
        await ctx.respond(embed=embed, ephemeral=True)
    
    @welcome.command(name="placeholders", description="Zeigt alle verfügbaren Placeholder")
    @commands.has_permissions(administrator=True)
    async def show_placeholders(self, ctx):
        """Zeigt alle verfügbaren Placeholder"""
        embed = discord.Embed(
            title="📝 Verfügbare Placeholder",
            description="Diese Placeholder können in Welcome Messages verwendet werden:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👤 User Informationen",
            value=(
                "`%user%` - Username (Display Name)\n"
                "`%username%` - Echter Username\n"
                "`%mention%` - User erwähnen (@User)\n"
                "`%tag%` - User#1234\n"
                "`%userid%` - User ID\n"
                "`%joindate%` - Beitrittsdatum\n"
                "`%createddate%` - Account Erstellungsdatum"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🏠 Server Informationen",
            value=(
                "`%servername%` - Servername\n"
                "`%server%` - Servername (Alternative)\n"
                "`%guild%` - Servername (Alternative)\n"
                "`%serverid%` - Server ID\n"
                "`%membercount%` - Mitgliederanzahl"
            ),
            inline=False
        )
        
        embed.set_footer(text="Beispiel: Willkommen %mention% auf %servername%! Du bist Mitglied #%membercount%")
        
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(WelcomeSystem(bot))