# Copyright (c) 2025 OPPRO.NET Network
from src.DevTools import TempVCDatabase
from src.DevTools import discord, commands, option, slash_command, ezcord, SlashCommandGroup
from src.DevTools import emoji_yes, emoji_no
from discord.ui import Container

db = TempVCDatabase()


class TempChannelControlView(discord.ui.View):
    def __init__(self, channel_owner_id: int, prefix: str = "🔧"):
        super().__init__(timeout=None)
        self.channel_owner_id = channel_owner_id
        self.prefix = prefix
        
        # Update button labels with custom prefix
        self.rename_button.label = f"{prefix} Umbenennen"
        self.limit_button.label = f"{prefix} Limit"
        self.lock_button.label = f"{prefix} Sperren"
        self.kick_button.label = f"{prefix} Kick"

    @discord.ui.button(label="🔧 Umbenennen", style=discord.ButtonStyle.primary, custom_id="tempvc_rename")
    async def rename_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.channel_owner_id:
            container = Container()
            container.add_text(f"{emoji_no} Keine Berechtigung\nDu bist nicht der Besitzer dieses Channels!")
            return await interaction.response.send_message(view=container, ephemeral=True)
        
        modal = RenameChannelModal(interaction.channel)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔧 Limit", style=discord.ButtonStyle.primary, custom_id="tempvc_limit")
    async def limit_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.channel_owner_id:
            container = Container()
            container.add_text(f"{emoji_no} Keine Berechtigung\nDu bist nicht der Besitzer dieses Channels!")
            return await interaction.response.send_message(view=container, ephemeral=True)
            
        modal = UserLimitModal(interaction.channel)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔧 Sperren", style=discord.ButtonStyle.secondary, custom_id="tempvc_lock")
    async def lock_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.channel_owner_id:
            container = Container()
            container.add_text(f"{emoji_no} Keine Berechtigung\nDu bist nicht der Besitzer dieses Channels!")
            return await interaction.response.send_message(view=container, ephemeral=True)
        
        channel = interaction.channel
        overwrites = channel.overwrites
        
        # Toggle lock status
        is_locked = not overwrites.get(interaction.guild.default_role, discord.PermissionOverwrite()).connect
        
        if interaction.guild.default_role not in overwrites:
            overwrites[interaction.guild.default_role] = discord.PermissionOverwrite()
        
        overwrites[interaction.guild.default_role].connect = not is_locked
        
        try:
            await channel.edit(overwrites=overwrites)
            status = "🔒 gesperrt" if is_locked else "🔓 entsperrt"
            button.label = f"{self.prefix} {'Entsperren' if is_locked else 'Sperren'}"
            button.style = discord.ButtonStyle.danger if is_locked else discord.ButtonStyle.secondary
            
            await interaction.response.edit_message(view=self)
            
            container = Container()
            container.add_text(f"Channel wurde {status}!")
            await interaction.followup.send(view=container, ephemeral=True)
        except discord.Forbidden:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nFehlende Berechtigungen!")
            await interaction.response.send_message(view=container, ephemeral=True)

    @discord.ui.button(label="🔧 Kick", style=discord.ButtonStyle.danger, custom_id="tempvc_kick")
    async def kick_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.channel_owner_id:
            container = Container()
            container.add_text(f"{emoji_no} Keine Berechtigung\nDu bist nicht der Besitzer dieses Channels!")
            return await interaction.response.send_message(view=container, ephemeral=True)
            
        modal = KickUserModal(interaction.channel)
        await interaction.response.send_modal(modal)


class RenameChannelModal(discord.ui.Modal):
    def __init__(self, channel):
        super().__init__(title="Channel umbenennen")
        self.channel = channel
        
        self.name_input = discord.ui.InputText(
            label="Neuer Channel-Name",
            placeholder="Gib einen neuen Namen ein...",
            value=channel.name,
            max_length=100,
            required=True
        )
        self.add_item(self.name_input)

    async def callback(self, interaction: discord.Interaction):
        new_name = self.name_input.value.strip()
        
        # Validate name
        if len(new_name) < 1:
            container = Container()
            container.add_text(f"{emoji_no} Ungültiger Name\nName darf nicht leer sein!")
            return await interaction.response.send_message(view=container, ephemeral=True)
            
        # Check for forbidden characters
        forbidden_chars = ['@', '#', ':', '`', '```']
        if any(char in new_name for char in forbidden_chars):
            container = Container()
            container.add_text(f"{emoji_no} Ungültige Zeichen\nName enthält ungültige Zeichen!")
            return await interaction.response.send_message(view=container, ephemeral=True)
        
        try:
            old_name = self.channel.name
            await self.channel.edit(name=new_name)
            
            container = Container()
            container.add_text(
                f"{emoji_yes} Channel umbenannt\n"
                f"**{old_name}** → **{new_name}**"
            )
            await interaction.response.send_message(view=container, ephemeral=True)
            
        except discord.Forbidden:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nFehlende Berechtigungen zum Umbenennen!")
            await interaction.response.send_message(view=container, ephemeral=True)
        except discord.HTTPException as e:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nFehler beim Umbenennen: {str(e)}")
            await interaction.response.send_message(view=container, ephemeral=True)


class UserLimitModal(discord.ui.Modal):
    def __init__(self, channel):
        super().__init__(title="User-Limit setzen")
        self.channel = channel
        
        current_limit = channel.user_limit if channel.user_limit else "Kein Limit"
        
        self.limit_input = discord.ui.InputText(
            label="Neues User-Limit (0 = Kein Limit)",
            placeholder="Gib eine Zahl zwischen 0-99 ein...",
            value=str(current_limit) if isinstance(current_limit, int) else "0",
            max_length=2,
            required=True
        )
        self.add_item(self.limit_input)

    async def callback(self, interaction: discord.Interaction):
        try:
            limit = int(self.limit_input.value.strip())
            
            if limit < 0 or limit > 99:
                container = Container()
                container.add_text(f"{emoji_no} Ungültiges Limit\nLimit muss zwischen 0 und 99 liegen!")
                return await interaction.response.send_message(view=container, ephemeral=True)
                
            # 0 means no limit in Discord
            limit = None if limit == 0 else limit
            
            await self.channel.edit(user_limit=limit)
            
            limit_text = "Kein Limit" if limit is None else f"{limit} User"
            
            container = Container()
            container.add_text(
                f"{emoji_yes} User-Limit geändert\n"
                f"Neues Limit: **{limit_text}**"
            )
            await interaction.response.send_message(view=container, ephemeral=True)
            
        except ValueError:
            container = Container()
            container.add_text(f"{emoji_no} Ungültige Eingabe\nBitte gib eine gültige Zahl ein!")
            await interaction.response.send_message(view=container, ephemeral=True)
        except discord.Forbidden:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nFehlende Berechtigungen!")
            await interaction.response.send_message(view=container, ephemeral=True)
        except discord.HTTPException as e:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nFehler beim Setzen des Limits: {str(e)}")
            await interaction.response.send_message(view=container, ephemeral=True)


class KickUserModal(discord.ui.Modal):
    def __init__(self, channel):
        super().__init__(title="User kicken")
        self.channel = channel
        
        # Create list of current members (except bot and channel owner)
        members_list = []
        for member in channel.members:
            if not member.bot and db.get_temp_channel_owner(channel.id) != member.id:
                members_list.append(f"{member.display_name} ({member.id})")
        
        members_text = "\n".join(members_list[:10])  # Limit to first 10 for display
        if len(members_list) > 10:
            members_text += f"\n... und {len(members_list) - 10} weitere"
        
        self.user_input = discord.ui.InputText(
            label="User zum Kicken",
            placeholder="@Username oder User-ID...",
            style=discord.InputTextStyle.short,
            required=True
        )
        self.add_item(self.user_input)
        
        if members_text:
            self.info_input = discord.ui.InputText(
                label="Aktuelle Mitglieder:",
                value=members_text if members_text else "Keine anderen Mitglieder im Channel",
                style=discord.InputTextStyle.paragraph,
                required=False
            )
            self.add_item(self.info_input)

    async def callback(self, interaction: discord.Interaction):
        user_input = self.user_input.value.strip()
        
        # Try to find user by mention, name or ID
        target_user = None
        
        # Check if it's a mention
        if user_input.startswith('<@') and user_input.endswith('>'):
            user_id = int(user_input[2:-1].replace('!', ''))
            target_user = interaction.guild.get_member(user_id)
        else:
            # Try by ID first
            try:
                user_id = int(user_input)
                target_user = interaction.guild.get_member(user_id)
            except ValueError:
                # Try by username/display name
                for member in self.channel.members:
                    if (member.display_name.lower() == user_input.lower() or 
                        member.name.lower() == user_input.lower()):
                        target_user = member
                        break
        
        if not target_user:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nUser nicht gefunden!")
            return await interaction.response.send_message(view=container, ephemeral=True)
            
        if target_user not in self.channel.members:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nUser ist nicht in diesem Channel!")
            return await interaction.response.send_message(view=container, ephemeral=True)
            
        if target_user.id == db.get_temp_channel_owner(self.channel.id):
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nDu kannst dich nicht selbst kicken!")
            return await interaction.response.send_message(view=container, ephemeral=True)
            
        if target_user.bot:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nBots können nicht gekickt werden!")
            return await interaction.response.send_message(view=container, ephemeral=True)
        
        try:
            await target_user.move_to(None)  # Disconnect from voice
            
            container = Container()
            container.add_text(
                f"{emoji_yes} User gekickt\n"
                f"**{target_user.display_name}** wurde aus dem Channel gekickt."
            )
            await interaction.response.send_message(view=container, ephemeral=True)
            
        except discord.Forbidden:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nFehlende Berechtigungen zum Kicken!")
            await interaction.response.send_message(view=container, ephemeral=True)
        except discord.HTTPException as e:
            container = Container()
            container.add_text(f"{emoji_no} Fehler\nFehler beim Kicken: {str(e)}")
            await interaction.response.send_message(view=container, ephemeral=True)


class TempVC(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    tempvc = SlashCommandGroup("tempvc", "Verwalte temporäre Voice-Channel Systeme")
    
    @tempvc.command(name="create", description="Erstelle ein VC-Erstellungssystem")
    @option("creator_channel", description="Channel, den Mitglieder betreten, um ihren VC zu erstellen",
            channel_types=[discord.ChannelType.voice])
    @option("category", description="Kategorie, in der die Temp-Channels erstellt werden",
            channel_types=[discord.ChannelType.category])
    async def tempvc_create(self, ctx: discord.ApplicationContext, creator_channel: discord.VoiceChannel,
                            category: discord.CategoryChannel):
        if not ctx.author.guild_permissions.administrator:
            container = Container()
            container.add_text(
                f"{emoji_no} Keine Berechtigung\n"
                "Du brauchst Administratorrechte."
            )
            return await ctx.respond(view=container, ephemeral=True)

        try:
            db.set_tempvc_settings(ctx.guild.id, creator_channel.id, category.id)
            
            container = Container()
            container.add_text(
                f"{emoji_yes} Temp-VC System aktiviert\n"
                "Das temporäre Voice-Channel System wurde erfolgreich eingerichtet!"
            )
            container.add_separator()
            container.add_text(
                f"**🎤 Ersteller-Channel:** {creator_channel.mention}\n"
                f"**📁 Kategorie:** {category.mention}\n"
                "**ℹ️ Information:** Mitglieder können nun den Ersteller-Channel betreten, um automatisch einen eigenen temporären Voice-Channel zu erhalten."
            )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)
        except Exception as e:
            container = Container()
            container.add_text(
                f"{emoji_no} Fehler beim Erstellen\n"
                f"```{str(e)}```"
            )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)

    @tempvc.command(name="remove", description="Entferne das VC-Erstellungssystem")
    async def tempvc_remove(self, ctx: discord.ApplicationContext):
        if not ctx.author.guild_permissions.administrator:
            container = Container()
            container.add_text(
                f"{emoji_no} Keine Berechtigung\n"
                "Du brauchst Administratorrechte."
            )
            view = discord.ui.View(container, timeout=None)
            return await ctx.respond(view=view, ephemeral=True)

        try:
            settings = db.get_tempvc_settings(ctx.guild.id)
            if not settings:
                container = Container()
                container.add_text(
                    f"{emoji_no} Kein System aktiv\n"
                    "Es ist derzeit kein Temp-VC System auf diesem Server aktiv."
                )
                view = discord.ui.View(container, timeout=None)
                return await ctx.respond(view=view, ephemeral=True)

            db.remove_tempvc_settings(ctx.guild.id)

            container = Container()
            container.add_text(
                f"{emoji_yes} System deaktiviert\n"
                "Das Temp-VC System wurde erfolgreich deaktiviert!"
            )
            container.add_separator()
            container.add_text(
                "**ℹ️ Information:** Bestehende temporäre Channels bleiben bestehen, aber es werden keine neuen mehr erstellt."
            )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)
        except Exception as e:
            container = Container()
            container.add_text(
                f"{emoji_no} Fehler beim Entfernen\n"
                f"```{str(e)}```"
            )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)

    @tempvc.command(name="settings", description="Zeige die aktuellen Temp-VC Einstellungen")
    async def tempvc_settings(self, ctx: discord.ApplicationContext):
        if not ctx.author.guild_permissions.administrator:
            container = Container()
            container.add_text(
                f"{emoji_no} Keine Berechtigung\n"
                "Du brauchst Administratorrechte."
            )
            view = discord.ui.View(container, timeout=None)
            return await ctx.respond(view=view, ephemeral=True)

        settings = db.get_tempvc_settings(ctx.guild.id)
        if not settings:
            container = Container()
            container.add_text(
                f"{emoji_no} Kein System aktiv\n"
                "Es ist derzeit kein Temp-VC System auf diesem Server aktiv."
            )
            container.add_separator()
            container.add_text(
                "**💡 Tipp:** Verwende `/tempvc create` um ein Temp-VC System einzurichten."
            )
            view = discord.ui.View(container, timeout=None)
            return await ctx.respond(view=view, ephemeral=True)

        creator_channel_id, category_id, auto_delete_time = settings
        creator_channel = ctx.guild.get_channel(creator_channel_id)
        category = ctx.guild.get_channel(category_id)

        container = Container()
        container.add_text("🎛️ **Temp-VC Einstellungen**\nAktuelle Konfiguration des temporären Voice-Channel Systems")
        container.add_separator()
        
        container.add_text(
            f"**🎤 Ersteller-Channel:**\n"
            f"{creator_channel.mention if creator_channel else f'{emoji_no} Channel nicht gefunden (ID: {creator_channel_id})'}"
        )
        container.add_separator()
        
        container.add_text(
            f"**📁 Kategorie:**\n"
            f"{category.mention if category else f'{emoji_no} Kategorie nicht gefunden (ID: {category_id})'}"
        )
        container.add_separator()
        
        container.add_text(f"**⏰ Auto-Löschzeit:**\n{auto_delete_time} Minuten")
        container.add_separator()
        
        # UI Settings
        ui_settings = db.get_ui_settings(ctx.guild.id)
        if ui_settings:
            ui_enabled, ui_prefix = ui_settings
            container.add_text(
                f"**🖥️ Control-UI:**\n"
                f"{'✅ Aktiviert' if ui_enabled else '❌ Deaktiviert'}"
            )
            if ui_enabled:
                container.add_separator()
                container.add_text(f"**🏷️ UI-Prefix:**\n{ui_prefix}")
        else:
            container.add_text("**🖥️ Control-UI:**\n❌ Deaktiviert")
        
        container.add_separator()
        container.add_text(
            f"**ℹ️ Status:**\n"
            f"{emoji_yes + ' System aktiv' if creator_channel and category else emoji_no + ' Fehlerhafte Konfiguration'}"
        )
        view = discord.ui.View(container, timeout=None)
        await ctx.respond(view=view, ephemeral=True)

    @tempvc.command(name="ui", description="Konfiguriere das Control-UI für Temp-Channels")
    @option("enabled", description="Soll das UI aktiviert sein?", choices=[
        discord.OptionChoice(name="Aktiviert", value="true"),
        discord.OptionChoice(name="Deaktiviert", value="false")
    ])
    @option("prefix", description="Prefix für UI-Buttons (Emoji oder Text)", required=False, default="🔧")
    async def tempvc_ui(self, ctx: discord.ApplicationContext, enabled: str, prefix: str = "🔧"):
        if not ctx.author.guild_permissions.administrator:
            container = Container()
            container.add_text(
                f"{emoji_no} Keine Berechtigung\n"
                "Du brauchst Administratorrechte."
            )
            return await ctx.respond(view=container, ephemeral=True)

        # Check if TempVC system exists
        settings = db.get_tempvc_settings(ctx.guild.id)
        if not settings:
            container = Container()
            container.add_text(
                f"{emoji_no} Kein System aktiv\n"
                "Du musst zuerst ein Temp-VC System erstellen!"
            )
            container.add_separator()
            container.add_text(
                "**💡 Tipp:** Verwende `/tempvc create` um ein Temp-VC System einzurichten."
            )
            view = discord.ui.View(container, timeout=None)
            return await ctx.respond(view=view, ephemeral=True)

        ui_enabled = enabled == "true"
        
        # Validate prefix
        if len(prefix) > 10:
            container = Container()
            container.add_text(f"{emoji_no} Ungültiger Prefix\nPrefix darf maximal 10 Zeichen lang sein!")
            return await ctx.respond(view=container, ephemeral=True)

        try:
            db.set_ui_settings(ctx.guild.id, ui_enabled, prefix)
            
            container = Container()
            container.add_text(f"{emoji_yes} UI-Einstellungen gespeichert")
            container.add_separator()
            container.add_text(
                f"**🖥️ Control-UI:** {'✅ Aktiviert' if ui_enabled else '❌ Deaktiviert'}"
            )
            if ui_enabled:
                container.add_separator()
                container.add_text(f"**🏷️ Prefix:** {prefix}")
                container.add_separator()
                container.add_text(
                    "**ℹ️ Information:** Das Control-UI wird nun in neu erstellten Temp-Channels angezeigt."
                )
            view = discord.ui.View(container, timeout=None)
            await ctx.respond(view=view, ephemeral=True)
            
        except Exception as e:
            container = Container()
            container.add_text(
                f"{emoji_no} Fehler beim Speichern\n"
                f"```{str(e)}```"
            )
            await ctx.respond(view=container, ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            if after.channel:
                await self.handle_creator_channel_join(member, after.channel)
            if before.channel:
                await self.handle_channel_leave(before.channel)
        except Exception as e:
            print(f"Error in voice state update: {e}")

    async def handle_creator_channel_join(self, member: discord.Member, channel: discord.VoiceChannel):
        settings = db.get_tempvc_settings(member.guild.id)
        if not settings:
            return

        creator_channel_id, category_id, auto_delete_time = settings

        if channel.id != creator_channel_id:
            return

        guild = member.guild
        category = discord.utils.get(guild.categories, id=category_id)
        if not category:
            print(f"Category with ID {category_id} not found in guild {guild.id}")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_permissions=True,
                move_members=True
            )
        }

        try:
            temp_channel = await guild.create_voice_channel(
                name=f"🔊 {member.display_name}'s Raum",
                category=category,
                overwrites=overwrites
            )
            db.add_temp_channel(temp_channel.id, guild.id, member.id)
            await member.move_to(temp_channel)

            # Check if UI is enabled and send control panel
            ui_settings = db.get_ui_settings(guild.id)
            if ui_settings and ui_settings[0]:  # UI enabled
                ui_enabled, ui_prefix = ui_settings
                
                container = Container()
                container.add_text(
                    f"## 🎛️ **Channel-Kontrolle**\n"
                    f"**{member.display_name}**, du bist der Besitzer dieses Channels!\n"
                    "Verwende die Buttons unten, um deinen Channel zu verwalten."
                )
                container.add_separator()
                container.add_text(
                    "**🔧 Verfügbare Aktionen:**\n"
                    "• **Umbenennen** - Ändere den Channel-Namen\n"
                    "• **Limit** - Setze ein User-Limit\n"
                    "• **Sperren** - Sperre/Entsperre den Channel\n"
                    "• **Kick** - Kicke User aus dem Channel"
                )
                container.add_separator()
                container.add_text("Diese Buttons funktionieren nur für den Channel-Besitzer.")
                
                control_view = TempChannelControlView(member.id, ui_prefix)
                view = discord.ui.View(container, timeout=None)
                await temp_channel.send(view=view)
                await temp_channel.send(view=control_view)

        except discord.Forbidden:
            print(f"Missing permissions to create voice channel in guild {guild.id}")
        except discord.HTTPException as e:
            print(f"HTTP error when creating voice channel: {e}")
        except Exception as e:
            print(f"Unexpected error when creating temp channel: {e}")

    async def handle_channel_leave(self, channel: discord.VoiceChannel):
        if len(channel.members) > 0:
            return

        if not db.is_temp_channel(channel.id):
            return

        try:
            db.remove_temp_channel(channel.id)
            await channel.delete(reason="Temp channel cleanup - channel empty")

        except discord.Forbidden:
            print(f"Missing permissions to delete channel {channel.id}")
        except discord.NotFound:
            db.remove_temp_channel(channel.id)
        except Exception as e:
            print(f"Error deleting temp channel {channel.id}: {e}")


def setup(bot):
    bot.add_cog(TempVC(bot))