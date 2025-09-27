import discord
from discord import slash_command, Option, SlashCommandGroup
from discord.ext import commands
import ezcord
from datetime import datetime, timezone
import logging

class UserManagement(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    user = SlashCommandGroup("user", "Erweiterte Benutzerverwaltung")

    @user.command(description="Zeigt detaillierte Informationen über einen Benutzer an")
    async def info(self, ctx, user: Option(discord.User, "Der Benutzer, über den du Informationen erhalten möchtest", default=None)):
        # Wenn kein Benutzer angegeben wurde, zeige Informationen über den Autor
        target_user = user or ctx.author
        
        try:
            # Versuche den Benutzer als Member zu bekommen für erweiterte Informationen
            if isinstance(target_user, discord.User):
                member = ctx.guild.get_member(target_user.id) if ctx.guild else None
            else:
                member = target_user

            embed = discord.Embed(
                title=f"📋 Informationen über {target_user.display_name}",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Grundlegende Informationen
            embed.add_field(name="👤 Benutzername", value=f"{target_user.name}#{target_user.discriminator}", inline=True)
            embed.add_field(name="🆔 ID", value=target_user.id, inline=True)
            embed.add_field(name="🤖 Bot", value="Ja" if target_user.bot else "Nein", inline=True)
            
            # Account-Erstellung
            created_at = target_user.created_at
            embed.add_field(
                name="📅 Account erstellt", 
                value=f"{created_at.strftime('%d.%m.%Y')}\n(<t:{int(created_at.timestamp())}:R>)", 
                inline=True
            )
            
            # Server-spezifische Informationen (nur wenn Member)
            if member:
                embed.add_field(name="📱 Status", value=str(member.status).capitalize(), inline=True)
                
                if member.joined_at:
                    joined_at = member.joined_at
                    embed.add_field(
                        name="📥 Server beigetreten", 
                        value=f"{joined_at.strftime('%d.%m.%Y')}\n(<t:{int(joined_at.timestamp())}:R>)", 
                        inline=True
                    )
                
                # Rollen (nur die wichtigsten anzeigen)
                roles = [role for role in member.roles[1:] if role.name != "@everyone"][:5]
                if roles:
                    embed.add_field(
                        name=f"🏷️ Rollen ({len(member.roles)-1} gesamt)", 
                        value=", ".join(role.mention for role in roles) + ("..." if len(member.roles) > 6 else ""),
                        inline=False
                    )
                
                # Höchste Rolle
                if member.top_role.name != "@everyone":
                    embed.add_field(name="⭐ Höchste Rolle", value=member.top_role.mention, inline=True)
                
                # Nickname
                if member.nick:
                    embed.add_field(name="📝 Nickname", value=member.nick, inline=True)
            
            # Gemeinsame Server
            mutual_guilds = len(target_user.mutual_guilds) if hasattr(target_user, 'mutual_guilds') else "Unbekannt"
            embed.add_field(name="🌐 Gemeinsame Server", value=str(mutual_guilds), inline=True)
            
            # Avatar
            if target_user.avatar:
                embed.set_thumbnail(url=target_user.avatar.url)
                embed.add_field(name="🖼️ Avatar", value=f"[Link]({target_user.avatar.url})", inline=True)
            else:
                embed.set_thumbnail(url=target_user.default_avatar.url)
                embed.add_field(name="🖼️ Avatar", value="Standard Avatar", inline=True)
            
            embed.set_footer(
                text=f"Angefordert von {ctx.author.display_name}", 
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logging.error(f"Fehler in user info command: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Abrufen der Benutzerinformationen.", ephemeral=True)

    @user.command(description="Zeigt alle Rollen eines Benutzers an")
    async def roles(self, ctx, user: Option(discord.Member, "Der Benutzer, dessen Rollen du sehen möchtest", default=None)):
        target_user = user or ctx.author
        
        try:
            roles = [role for role in target_user.roles[1:] if role.name != "@everyone"]
            
            if not roles:
                embed = discord.Embed(
                    title="🏷️ Rollen",
                    description=f"{target_user.display_name} hat keine besonderen Rollen.",
                    color=discord.Color.orange()
                )
                await ctx.respond(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"🏷️ Rollen von {target_user.display_name}",
                color=target_user.top_role.color or discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Rollen nach Hierarchie sortieren
            roles.sort(key=lambda x: x.position, reverse=True)
            
            role_list = []
            for i, role in enumerate(roles, 1):
                permissions_count = sum(1 for perm, value in role.permissions if value)
                role_list.append(f"{i}. {role.mention} (Pos: {role.position}, Perms: {permissions_count})")
            
            # Aufteilen in Chunks falls zu viele Rollen
            chunk_size = 10
            for i in range(0, len(role_list), chunk_size):
                chunk = role_list[i:i+chunk_size]
                field_name = "Rollen" if i == 0 else f"Rollen (Fortsetzung)"
                embed.add_field(name=field_name, value="\n".join(chunk), inline=False)
            
            embed.set_footer(text=f"Gesamt: {len(roles)} Rollen")
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logging.error(f"Fehler in user roles command: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Abrufen der Rollen.", ephemeral=True)

    @user.command(description="Setzt den Nicknamen eines Benutzers")
    @discord.default_permissions(manage_nicknames=True)
    async def set_nickname(self, ctx, user: Option(discord.Member, "Der Benutzer, dessen Nicknamen du ändern möchtest"), nickname: Option(str, "Der neue Nickname (leer lassen zum Entfernen)", required=False)):
        try:
            # Berechtigungsprüfungen
            if not ctx.author.guild_permissions.manage_nicknames:
                await ctx.respond("❌ Du hast keine Berechtigung, Nicknames zu verwalten.", ephemeral=True)
                return
            
            if user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                await ctx.respond("❌ Du kannst den Nickname dieses Benutzers nicht ändern (höhere Rolle).", ephemeral=True)
                return
            
            if user == ctx.guild.owner:
                await ctx.respond("❌ Der Nickname des Server-Besitzers kann nicht geändert werden.", ephemeral=True)
                return
            
            # Nickname validieren
            if nickname and len(nickname) > 32:
                await ctx.respond("❌ Der Nickname ist zu lang (maximal 32 Zeichen).", ephemeral=True)
                return
            
            old_nick = user.display_name
            await user.edit(nick=nickname, reason=f"Nickname geändert von {ctx.author}")
            
            embed = discord.Embed(
                title="✅ Nickname geändert",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Benutzer", value=user.mention, inline=True)
            embed.add_field(name="Vorher", value=old_nick, inline=True)
            embed.add_field(name="Nachher", value=nickname or user.name, inline=True)
            embed.set_footer(text=f"Geändert von {ctx.author.display_name}")
            
            await ctx.respond(embed=embed)
            
        except discord.Forbidden:
            await ctx.respond("❌ Ich habe keine Berechtigung, den Nickname zu ändern.", ephemeral=True)
        except Exception as e:
            logging.error(f"Fehler beim Setzen des Nicknames: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Ändern des Nicknames.", ephemeral=True)

    @user.command(description="Entfernt alle Rollen eines Benutzers")
    @discord.default_permissions(manage_roles=True)
    async def remove_roles(self, ctx, user: Option(discord.Member, "Der Benutzer, dessen Rollen du entfernen möchtest"), reason: Option(str, "Grund für die Aktion", required=False)):
        try:
            # Berechtigungsprüfungen
            if not ctx.author.guild_permissions.manage_roles:
                await ctx.respond("❌ Du hast keine Berechtigung, Rollen zu verwalten.", ephemeral=True)
                return
            
            if user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                await ctx.respond("❌ Du kannst die Rollen dieses Benutzers nicht verwalten (höhere Rolle).", ephemeral=True)
                return
            
            if user == ctx.guild.owner:
                await ctx.respond("❌ Die Rollen des Server-Besitzers können nicht entfernt werden.", ephemeral=True)
                return
            
            removable_roles = [role for role in user.roles[1:] if role < ctx.me.top_role]
            
            if not removable_roles:
                await ctx.respond("❌ Keine Rollen zum Entfernen gefunden oder Bot hat unzureichende Berechtigungen.", ephemeral=True)
                return
            
            # Bestätigung anfordern
            embed = discord.Embed(
                title="⚠️ Rollen entfernen bestätigen",
                description=f"Möchtest du wirklich **{len(removable_roles)} Rollen** von {user.mention} entfernen?\n\n**Rollen:** {', '.join(role.name for role in removable_roles[:5])}{'...' if len(removable_roles) > 5 else ''}",
                color=discord.Color.orange()
            )
            
            view = ConfirmationView()
            await ctx.respond(embed=embed, view=view, ephemeral=True)
            await view.wait()
            
            if view.value:
                audit_reason = f"Alle Rollen entfernt von {ctx.author}" + (f" | Grund: {reason}" if reason else "")
                await user.remove_roles(*removable_roles, reason=audit_reason)
                
                embed = discord.Embed(
                    title="✅ Rollen entfernt",
                    description=f"**{len(removable_roles)} Rollen** wurden von {user.mention} entfernt.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text=f"Entfernt von {ctx.author.display_name}")
                await ctx.edit(embed=embed, view=None)
            else:
                embed = discord.Embed(
                    title="❌ Abgebrochen",
                    description="Die Aktion wurde abgebrochen.",
                    color=discord.Color.red()
                )
                await ctx.edit(embed=embed, view=None)
                
        except discord.Forbidden:
            await ctx.respond("❌ Ich habe keine Berechtigung, diese Rollen zu entfernen.", ephemeral=True)
        except Exception as e:
            logging.error(f"Fehler beim Entfernen der Rollen: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Entfernen der Rollen.", ephemeral=True)

    @user.command(description="Gibt einem Benutzer eine Rolle")
    @discord.default_permissions(manage_roles=True)
    async def give_role(self, ctx, user: Option(discord.Member, "Der Benutzer, dem du eine Rolle geben möchtest"), role: Option(discord.Role, "Die Rolle, die du vergeben möchtest"), reason: Option(str, "Grund für die Rollenvergabe", required=False)):
        try:
            # Berechtigungsprüfungen
            if not ctx.author.guild_permissions.manage_roles:
                await ctx.respond("❌ Du hast keine Berechtigung, Rollen zu verwalten.", ephemeral=True)
                return
            
            if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                await ctx.respond("❌ Du kannst diese Rolle nicht vergeben (Rolle ist höher als deine).", ephemeral=True)
                return
            
            if role >= ctx.me.top_role:
                await ctx.respond("❌ Ich kann diese Rolle nicht vergeben (Rolle ist höher als meine).", ephemeral=True)
                return
            
            if role in user.roles:
                await ctx.respond(f"❌ {user.display_name} hat bereits die Rolle {role.mention}.", ephemeral=True)
                return
            
            audit_reason = f"Rolle vergeben von {ctx.author}" + (f" | Grund: {reason}" if reason else "")
            await user.add_roles(role, reason=audit_reason)
            
            embed = discord.Embed(
                title="✅ Rolle vergeben",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Benutzer", value=user.mention, inline=True)
            embed.add_field(name="Rolle", value=role.mention, inline=True)
            if reason:
                embed.add_field(name="Grund", value=reason, inline=False)
            embed.set_footer(text=f"Vergeben von {ctx.author.display_name}")
            
            await ctx.respond(embed=embed)
            
        except discord.Forbidden:
            await ctx.respond("❌ Ich habe keine Berechtigung, diese Rolle zu vergeben.", ephemeral=True)
        except Exception as e:
            logging.error(f"Fehler beim Vergeben der Rolle: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Vergeben der Rolle.", ephemeral=True)

    @user.command(description="Entfernt eine Rolle von einem Benutzer")
    @discord.default_permissions(manage_roles=True)
    async def remove_role(self, ctx, user: Option(discord.Member, "Der Benutzer, von dem du eine Rolle entfernen möchtest"), role: Option(discord.Role, "Die Rolle, die du entfernen möchtest"), reason: Option(str, "Grund für die Entfernung", required=False)):
        try:
            # Berechtigungsprüfungen
            if not ctx.author.guild_permissions.manage_roles:
                await ctx.respond("❌ Du hast keine Berechtigung, Rollen zu verwalten.", ephemeral=True)
                return
            
            if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                await ctx.respond("❌ Du kannst diese Rolle nicht entfernen (Rolle ist höher als deine).", ephemeral=True)
                return
            
            if role >= ctx.me.top_role:
                await ctx.respond("❌ Ich kann diese Rolle nicht entfernen (Rolle ist höher als meine).", ephemeral=True)
                return
            
            if role not in user.roles:
                await ctx.respond(f"❌ {user.display_name} hat die Rolle {role.mention} nicht.", ephemeral=True)
                return
            
            audit_reason = f"Rolle entfernt von {ctx.author}" + (f" | Grund: {reason}" if reason else "")
            await user.remove_roles(role, reason=audit_reason)
            
            embed = discord.Embed(
                title="✅ Rolle entfernt",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Benutzer", value=user.mention, inline=True)
            embed.add_field(name="Rolle", value=role.mention, inline=True)
            if reason:
                embed.add_field(name="Grund", value=reason, inline=False)
            embed.set_footer(text=f"Entfernt von {ctx.author.display_name}")
            
            await ctx.respond(embed=embed)
            
        except discord.Forbidden:
            await ctx.respond("❌ Ich habe keine Berechtigung, diese Rolle zu entfernen.", ephemeral=True)
        except Exception as e:
            logging.error(f"Fehler beim Entfernen der Rolle: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Entfernen der Rolle.", ephemeral=True)

    @user.command(description="Zeigt die Berechtigungen eines Benutzers an")
    async def permissions(self, ctx, user: Option(discord.Member, "Der Benutzer, dessen Berechtigungen du sehen möchtest", default=None)):
        target_user = user or ctx.author
        
        try:
            permissions = target_user.guild_permissions
            
            embed = discord.Embed(
                title=f"🔐 Berechtigungen von {target_user.display_name}",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Wichtige Berechtigungen hervorheben
            admin_perms = []
            mod_perms = []
            basic_perms = []
            
            for perm, value in permissions:
                if not value:
                    continue
                    
                perm_name = perm.replace('_', ' ').title()
                
                if perm in ['administrator']:
                    admin_perms.append(perm_name)
                elif perm in ['manage_guild', 'manage_roles', 'manage_channels', 'ban_members', 'kick_members', 'manage_messages']:
                    mod_perms.append(perm_name)
                else:
                    basic_perms.append(perm_name)
            
            if admin_perms:
                embed.add_field(name="👑 Administrator", value="\n".join(admin_perms), inline=False)
            
            if mod_perms:
                embed.add_field(name="🛡️ Moderation", value="\n".join(mod_perms), inline=False)
            
            if basic_perms:
                # Nur die ersten 10 anzeigen
                basic_display = basic_perms[:10]
                if len(basic_perms) > 10:
                    basic_display.append(f"... und {len(basic_perms) - 10} weitere")
                embed.add_field(name="📝 Allgemein", value="\n".join(basic_display), inline=False)
            
            embed.set_footer(text=f"Gesamt: {sum(1 for _, value in permissions if value)} Berechtigungen")
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Berechtigungen: {e}")
            await ctx.respond("❌ Ein Fehler ist aufgetreten beim Abrufen der Berechtigungen.", ephemeral=True)


class ConfirmationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.value = None

    @discord.ui.button(label="Bestätigen", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()

    async def on_timeout(self):
        self.value = False
        self.stop()


def setup(bot):
    bot.add_cog(UserManagement(bot))