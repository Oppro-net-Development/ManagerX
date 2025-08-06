# anticapslock_cog.py
import discord
from discord.ext import commands
from FastCoding import AntiCapslockDatabase
import asyncio
from typing import Optional

class AntiCapslock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AntiCapslockDatabase()
    
    def is_caps_spam(self, message: str, threshold: int, min_length: int) -> bool:
        """Überprüft, ob eine Nachricht zu viele Großbuchstaben enthält"""
        if len(message) < min_length:
            return False
        
        # Entferne Leerzeichen und Sonderzeichen für die Berechnung
        letters_only = ''.join([c for c in message if c.isalpha()])
        if len(letters_only) == 0:
            return False
        
        caps_count = sum(1 for c in letters_only if c.isupper())
        caps_percentage = (caps_count / len(letters_only)) * 100
        
        return caps_percentage >= threshold
    
    def has_permission(self, member: discord.Member, config: dict) -> bool:
        """Überprüft, ob ein Mitglied die Berechtigung hat, das System zu umgehen"""
        if config["ignore_admins"] and member.guild_permissions.administrator:
            return True
        
        whitelist_roles = config.get("whitelist_roles", [])
        for role in member.roles:
            if role.id in whitelist_roles:
                return True
        
        return False
    
    async def log_action(self, guild: discord.Guild, config: dict, action: str, user: discord.Member, message: discord.Message):
        """Loggt Aktionen in den Log-Channel"""
        log_channel_id = config.get("log_channel")
        if not log_channel_id:
            return
        
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🔠 AntiCapslock Aktion",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Aktion", value=action, inline=True)
        embed.add_field(name="Benutzer", value=f"{user.mention} ({user.id})", inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Nachricht", value=message.content[:1000] + ("..." if len(message.content) > 1000 else ""), inline=False)
        
        try:
            await log_channel.send(embed=embed)
        except discord.HTTPException:
            pass
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Event Handler für neue Nachrichten"""
        if message.author.bot or not message.guild:
            return
        
        config = self.db.get_guild_config(message.guild.id)
        if not config["enabled"]:
            return
        
        # Überprüfe Whitelist-Channels
        if message.channel.id in config.get("whitelist_channels", []):
            return
        
        # Überprüfe Berechtigungen
        if self.has_permission(message.author, config):
            return
        
        # Überprüfe auf Caps-Spam
        if not self.is_caps_spam(message.content, config["caps_threshold"], config["min_length"]):
            return
        
        # Führe Aktion aus
        action = config["action"]
        
        if action == "delete":
            try:
                await message.delete()
                await self.log_action(message.guild, config, "Nachricht gelöscht", message.author, message)
                
                # Sende Warnung per DM
                try:
                    embed = discord.Embed(
                        title="⚠️ Nachricht gelöscht",
                        description=f"Deine Nachricht in **{message.guild.name}** wurde gelöscht:\n\n{config['warning_message']}",
                        color=discord.Color.red()
                    )
                    await message.author.send(embed=embed)
                except discord.HTTPException:
                    pass
            except discord.HTTPException:
                pass
        
        elif action == "warn":
            warnings = self.db.add_warning(message.guild.id, message.author.id)
            
            embed = discord.Embed(
                title="⚠️ Warnung",
                description=config["warning_message"],
                color=discord.Color.yellow()
            )
            embed.add_field(name="Warnungen", value=f"{warnings}/{config['max_warnings']}", inline=True)
            
            try:
                await message.channel.send(f"{message.author.mention}", embed=embed, delete_after=10)
                await self.log_action(message.guild, config, f"Warnung ({warnings}/{config['max_warnings']})", message.author, message)
                
                # Bei max. Warnungen timeout
                if warnings >= config["max_warnings"]:
                    try:
                        timeout_duration = config.get("timeout_duration", 300)
                        await message.author.timeout(discord.utils.utcnow() + discord.timedelta(seconds=timeout_duration))
                        await self.log_action(message.guild, config, f"Timeout ({timeout_duration}s) - Max. Warnungen erreicht", message.author, message)
                        self.db.reset_warnings(message.guild.id, message.author.id)
                    except discord.HTTPException:
                        pass
            except discord.HTTPException:
                pass
        
        elif action == "timeout":
            try:
                timeout_duration = config.get("timeout_duration", 300)
                await message.author.timeout(discord.utils.utcnow() + discord.timedelta(seconds=timeout_duration))
                await self.log_action(message.guild, config, f"Timeout ({timeout_duration}s)", message.author, message)
                
                embed = discord.Embed(
                    title="🔇 Timeout",
                    description=f"{message.author.mention} wurde für {timeout_duration} Sekunden stumm geschaltet.\n\n{config['warning_message']}",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed, delete_after=15)
            except discord.HTTPException:
                pass
    
    @commands.group(name="anticaps", aliases=["ac"])
    @commands.has_permissions(administrator=True)
    async def anticaps(self, ctx):
        """AntiCapslock Konfiguration"""
        if ctx.invoked_subcommand is None:
            await self.show_config(ctx)
    
    async def show_config(self, ctx):
        """Zeigt die aktuelle Konfiguration"""
        config = self.db.get_guild_config(ctx.guild.id)
        
        embed = discord.Embed(
            title="🔠 AntiCapslock Konfiguration",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Status",
            value="🟢 Aktiviert" if config["enabled"] else "🔴 Deaktiviert",
            inline=True
        )
        embed.add_field(
            name="Caps Schwellenwert",
            value=f"{config['caps_threshold']}%",
            inline=True
        )
        embed.add_field(
            name="Min. Länge",
            value=f"{config['min_length']} Zeichen",
            inline=True
        )
        embed.add_field(
            name="Aktion",
            value=config["action"].title(),
            inline=True
        )
        embed.add_field(
            name="Max. Warnungen",
            value=config["max_warnings"],
            inline=True
        )
        embed.add_field(
            name="Timeout Dauer",
            value=f"{config['timeout_duration']}s",
            inline=True
        )
        embed.add_field(
            name="Admins ignorieren",
            value="✅" if config["ignore_admins"] else "❌",
            inline=True
        )
        
        log_channel = ctx.guild.get_channel(config.get("log_channel"))
        embed.add_field(
            name="Log Channel",
            value=log_channel.mention if log_channel else "Nicht gesetzt",
            inline=True
        )
        
        whitelist_channels = [ctx.guild.get_channel(ch_id) for ch_id in config.get("whitelist_channels", [])]
        whitelist_channels = [ch.mention for ch in whitelist_channels if ch]
        embed.add_field(
            name="Whitelist Channels",
            value="\n".join(whitelist_channels) if whitelist_channels else "Keine",
            inline=False
        )
        
        whitelist_roles = [ctx.guild.get_role(role_id) for role_id in config.get("whitelist_roles", [])]
        whitelist_roles = [role.mention for role in whitelist_roles if role]
        embed.add_field(
            name="Whitelist Rollen",
            value="\n".join(whitelist_roles) if whitelist_roles else "Keine",
            inline=False
        )
        
        embed.set_footer(text="Verwende /anticaps help für alle Befehle")
        await ctx.send(embed=embed)
    
    @anticaps.command(name="toggle")
    async def toggle(self, ctx):
        """Aktiviert/Deaktiviert das AntiCapslock System"""
        current = self.db.get_guild_config(ctx.guild.id)["enabled"]
        self.db.update_guild_setting(ctx.guild.id, "enabled", not current)
        
        status = "aktiviert" if not current else "deaktiviert"
        embed = discord.Embed(
            title="✅ Einstellung geändert",
            description=f"AntiCapslock wurde **{status}**.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="threshold")
    async def threshold(self, ctx, percentage: int):
        """Setzt den Caps-Schwellenwert (10-95%)"""
        if not 10 <= percentage <= 95:
            embed = discord.Embed(
                title="❌ Ungültiger Wert",
                description="Der Schwellenwert muss zwischen 10% und 95% liegen.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        self.db.update_guild_setting(ctx.guild.id, "caps_threshold", percentage)
        embed = discord.Embed(
            title="✅ Schwellenwert gesetzt",
            description=f"Caps-Schwellenwert wurde auf **{percentage}%** gesetzt.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="minlength")
    async def minlength(self, ctx, length: int):
        """Setzt die minimale Nachrichtenlänge (3-50)"""
        if not 3 <= length <= 50:
            embed = discord.Embed(
                title="❌ Ungültiger Wert",
                description="Die minimale Länge muss zwischen 3 und 50 Zeichen liegen.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        self.db.update_guild_setting(ctx.guild.id, "min_length", length)
        embed = discord.Embed(
            title="✅ Minimale Länge gesetzt",
            description=f"Minimale Nachrichtenlänge wurde auf **{length} Zeichen** gesetzt.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="action")
    async def action(self, ctx, action_type: str):
        """Setzt die Aktion (warn/delete/timeout)"""
        valid_actions = ["warn", "delete", "timeout"]
        if action_type.lower() not in valid_actions:
            embed = discord.Embed(
                title="❌ Ungültige Aktion",
                description=f"Gültige Aktionen: {', '.join(valid_actions)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        self.db.update_guild_setting(ctx.guild.id, "action", action_type.lower())
        embed = discord.Embed(
            title="✅ Aktion gesetzt",
            description=f"Aktion wurde auf **{action_type.lower()}** gesetzt.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="timeout")
    async def timeout_duration(self, ctx, seconds: int):
        """Setzt die Timeout-Dauer in Sekunden (60-3600)"""
        if not 60 <= seconds <= 3600:
            embed = discord.Embed(
                title="❌ Ungültiger Wert",
                description="Die Timeout-Dauer muss zwischen 60 und 3600 Sekunden (1-60 Minuten) liegen.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        self.db.update_guild_setting(ctx.guild.id, "timeout_duration", seconds)
        embed = discord.Embed(
            title="✅ Timeout-Dauer gesetzt",
            description=f"Timeout-Dauer wurde auf **{seconds} Sekunden** ({seconds//60} Min {seconds%60}s) gesetzt.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="maxwarnings")
    async def maxwarnings(self, ctx, count: int):
        """Setzt die maximale Anzahl Warnungen (1-10)"""
        if not 1 <= count <= 10:
            embed = discord.Embed(
                title="❌ Ungültiger Wert",
                description="Die maximale Anzahl Warnungen muss zwischen 1 und 10 liegen.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        self.db.update_guild_setting(ctx.guild.id, "max_warnings", count)
        embed = discord.Embed(
            title="✅ Max. Warnungen gesetzt",
            description=f"Maximale Anzahl Warnungen wurde auf **{count}** gesetzt.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="message")
    async def warning_message(self, ctx, *, message: str):
        """Setzt die Warnungsnachricht"""
        if len(message) > 500:
            embed = discord.Embed(
                title="❌ Nachricht zu lang",
                description="Die Warnungsnachricht darf maximal 500 Zeichen lang sein.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        self.db.update_guild_setting(ctx.guild.id, "warning_message", message)
        embed = discord.Embed(
            title="✅ Warnungsnachricht gesetzt",
            description=f"Warnungsnachricht wurde gesetzt:\n\n*{message}*",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="logchannel")
    async def logchannel(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Setzt den Log-Channel (oder entfernt ihn)"""
        if channel is None:
            self.db.update_guild_setting(ctx.guild.id, "log_channel", None)
            embed = discord.Embed(
                title="✅ Log-Channel entfernt",
                description="Log-Channel wurde entfernt.",
                color=discord.Color.green()
            )
        else:
            self.db.update_guild_setting(ctx.guild.id, "log_channel", channel.id)
            embed = discord.Embed(
                title="✅ Log-Channel gesetzt",
                description=f"Log-Channel wurde auf {channel.mention} gesetzt.",
                color=discord.Color.green()
            )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="whitelist")
    async def whitelist(self, ctx):
        """Whitelist Verwaltung"""
        embed = discord.Embed(
            title="🔠 Whitelist Befehle",
            description="Verwende diese Befehle zur Whitelist-Verwaltung:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Channels",
            value="`/anticaps whitelist channel add <#channel>`\n`/anticaps whitelist channel remove <#channel>`\n`/anticaps whitelist channel list`",
            inline=False
        )
        embed.add_field(
            name="Rollen",
            value="`/anticaps whitelist role add <@role>`\n`/anticaps whitelist role remove <@role>`\n`/anticaps whitelist role list`",
            inline=False
        )
        await ctx.send(embed=embed)
    
    @anticaps.group(name="whitelist")
    async def whitelist_group(self, ctx):
        """Whitelist Verwaltung"""
        if ctx.invoked_subcommand is None:
            await self.whitelist(ctx)
    
    @whitelist_group.group(name="channel")
    async def whitelist_channel(self, ctx):
        """Channel Whitelist Verwaltung"""
        pass
    
    @whitelist_channel.command(name="add")
    async def whitelist_channel_add(self, ctx, channel: discord.TextChannel):
        """Fügt einen Channel zur Whitelist hinzu"""
        config = self.db.get_guild_config(ctx.guild.id)
        whitelist = config.get("whitelist_channels", [])
        
        if channel.id in whitelist:
            embed = discord.Embed(
                title="❌ Channel bereits in Whitelist",
                description=f"{channel.mention} ist bereits in der Whitelist.",
                color=discord.Color.red()
            )
        else:
            whitelist.append(channel.id)
            self.db.update_guild_setting(ctx.guild.id, "whitelist_channels", whitelist)
            embed = discord.Embed(
                title="✅ Channel hinzugefügt",
                description=f"{channel.mention} wurde zur Whitelist hinzugefügt.",
                color=discord.Color.green()
            )
        await ctx.send(embed=embed)
    
    @whitelist_channel.command(name="remove")
    async def whitelist_channel_remove(self, ctx, channel: discord.TextChannel):
        """Entfernt einen Channel aus der Whitelist"""
        config = self.db.get_guild_config(ctx.guild.id)
        whitelist = config.get("whitelist_channels", [])
        
        if channel.id not in whitelist:
            embed = discord.Embed(
                title="❌ Channel nicht in Whitelist",
                description=f"{channel.mention} ist nicht in der Whitelist.",
                color=discord.Color.red()
            )
        else:
            whitelist.remove(channel.id)
            self.db.update_guild_setting(ctx.guild.id, "whitelist_channels", whitelist)
            embed = discord.Embed(
                title="✅ Channel entfernt",
                description=f"{channel.mention} wurde aus der Whitelist entfernt.",
                color=discord.Color.green()
            )
        await ctx.send(embed=embed)
    
    @whitelist_group.group(name="role")
    async def whitelist_role(self, ctx):
        """Rollen Whitelist Verwaltung"""
        pass
    
    @whitelist_role.command(name="add")
    async def whitelist_role_add(self, ctx, role: discord.Role):
        """Fügt eine Rolle zur Whitelist hinzu"""
        config = self.db.get_guild_config(ctx.guild.id)
        whitelist = config.get("whitelist_roles", [])
        
        if role.id in whitelist:
            embed = discord.Embed(
                title="❌ Rolle bereits in Whitelist",
                description=f"{role.mention} ist bereits in der Whitelist.",
                color=discord.Color.red()
            )
        else:
            whitelist.append(role.id)
            self.db.update_guild_setting(ctx.guild.id, "whitelist_roles", whitelist)
            embed = discord.Embed(
                title="✅ Rolle hinzugefügt",
                description=f"{role.mention} wurde zur Whitelist hinzugefügt.",
                color=discord.Color.green()
            )
        await ctx.send(embed=embed)
    
    @whitelist_role.command(name="remove")
    async def whitelist_role_remove(self, ctx, role: discord.Role):
        """Entfernt eine Rolle aus der Whitelist"""
        config = self.db.get_guild_config(ctx.guild.id)
        whitelist = config.get("whitelist_roles", [])
        
        if role.id not in whitelist:
            embed = discord.Embed(
                title="❌ Rolle nicht in Whitelist",
                description=f"{role.mention} ist nicht in der Whitelist.",
                color=discord.Color.red()
            )
        else:
            whitelist.remove(role.id)
            self.db.update_guild_setting(ctx.guild.id, "whitelist_roles", whitelist)
            embed = discord.Embed(
                title="✅ Rolle entfernt",
                description=f"{role.mention} wurde aus der Whitelist entfernt.",
                color=discord.Color.green()
            )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="reset")
    async def reset_warnings(self, ctx, user: discord.Member):
        """Setzt die Warnungen eines Users zurück"""
        self.db.reset_warnings(ctx.guild.id, user.id)
        embed = discord.Embed(
            title="✅ Warnungen zurückgesetzt",
            description=f"Warnungen für {user.mention} wurden zurückgesetzt.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="ignore_admins")
    async def ignore_admins(self, ctx):
        """Schaltet um, ob Administratoren ignoriert werden"""
        current = self.db.get_guild_config(ctx.guild.id)["ignore_admins"]
        self.db.update_guild_setting(ctx.guild.id, "ignore_admins", not current)
        
        status = "ignoriert" if not current else "nicht ignoriert"
        embed = discord.Embed(
            title="✅ Einstellung geändert",
            description=f"Administratoren werden nun **{status}**.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @anticaps.command(name="help")
    async def help_command(self, ctx):
        """Zeigt alle verfügbaren Befehle"""
        embed = discord.Embed(
            title="🔠 AntiCapslock Hilfe",
            description="Alle verfügbaren Befehle:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Grundeinstellungen",
            value="`/anticaps` - Zeige Konfiguration\n"
                  "`/anticaps toggle` - System an/ausschalten\n"
                  "`/anticaps threshold <10-95>` - Caps-Schwellenwert\n"
                  "`/anticaps minlength <3-50>` - Min. Nachrichtenlänge\n"
                  "`/anticaps action <warn/delete/timeout>` - Aktion\n"
                  "`/anticaps ignore_admins` - Admins ignorieren",
            inline=False
        )
        
        embed.add_field(
            name="Erweiterte Einstellungen",
            value="`/anticaps timeout <60-3600>` - Timeout-Dauer\n"
                  "`/anticaps maxwarnings <1-10>` - Max. Warnungen\n"
                  "`/anticaps message <text>` - Warnungsnachricht\n"
                  "`/anticaps logchannel <#channel>` - Log-Channel",
            inline=False
        )
        
        embed.add_field(
            name="Whitelist",
            value="`/anticaps whitelist channel add/remove <#channel>`\n"
                  "`/anticaps whitelist role add/remove <@role>`",
            inline=False
        )
        
        embed.add_field(
            name="Verwaltung",
            value="`/anticaps reset <@user>` - Warnungen zurücksetzen",
            inline=False
        )
        
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(AntiCapslock(bot))