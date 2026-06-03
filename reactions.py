import logging
from typing import Optional

import discord
from discord import ui

from models import ReactionRoleModel, ButtonRoleModel

logger = logging.getLogger(__name__)


class ButtonRoleView(ui.View):
    def __init__(self, buttons: list[dict]):
        super().__init__(timeout=None)
        for b in buttons:
            style_map = {
                'primary': discord.ButtonStyle.primary,
                'secondary': discord.ButtonStyle.secondary,
                'success': discord.ButtonStyle.success,
                'danger': discord.ButtonStyle.danger,
            }
            style = style_map.get(b.get('style', 'primary'), discord.ButtonStyle.primary)
            custom_id = f"br_{b['role_name']}_{b['guild_id']}"
            btn = ui.Button(label=b['label'], style=style, custom_id=custom_id)
            self.add_item(btn)


class ReactionRoleManager:
    def __init__(self):
        self.reaction_configs: dict[int, list[ReactionRoleModel]] = {}
        self.button_configs: dict[int, list[ButtonRoleModel]] = {}
        self._button_views: dict[int, ui.View] = {}

    def set_reaction_configs(self, guild_id: int, configs: list[ReactionRoleModel]):
        self.reaction_configs[guild_id] = configs

    def set_button_configs(self, guild_id: int, configs: list[ButtonRoleModel]):
        self.button_configs[guild_id] = configs

    def get_button_view(self, guild_id: int) -> Optional[ui.View]:
        configs = self.button_configs.get(guild_id, [])
        if not configs:
            return None
        buttons = [{'label': b.label, 'style': b.style, 'role_name': b.role, 'guild_id': guild_id} for b in configs]
        return ButtonRoleView(buttons)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent, bot: discord.Client):
        configs = self.reaction_configs.get(payload.guild_id, [])
        for rc in configs:
            channel = bot.get_channel(payload.channel_id)
            if channel and channel.name == rc.channel:
                guild = bot.get_guild(payload.guild_id)
                if guild:
                    role = discord.utils.get(guild.roles, name=rc.role)
                    member = guild.get_member(payload.user_id)
                    if role and member and not member.bot:
                        try:
                            await member.add_roles(role, reason="Reaction role")
                        except Exception as e:
                            logger.error(f"Reaction role add failed: {e}")

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent, bot: discord.Client):
        configs = self.reaction_configs.get(payload.guild_id, [])
        for rc in configs:
            channel = bot.get_channel(payload.channel_id)
            if channel and channel.name == rc.channel:
                guild = bot.get_guild(payload.guild_id)
                if guild:
                    role = discord.utils.get(guild.roles, name=rc.role)
                    member = guild.get_member(payload.user_id)
                    if role and member and not member.bot:
                        try:
                            await member.remove_roles(role, reason="Reaction role")
                        except Exception as e:
                            logger.error(f"Reaction role remove failed: {e}")

    async def on_button_interaction(self, interaction: discord.Interaction):
        custom_id = interaction.data.get('custom_id', '') if interaction.data else ''
        if not custom_id.startswith('br_'):
            return
        parts = custom_id.split('_', 2)
        if len(parts) < 3:
            return
        role_name = parts[1]
        guild = interaction.guild
        if not guild:
            return
        role = discord.utils.get(guild.roles, name=role_name)
        member = interaction.user
        if not role or not isinstance(member, discord.Member):
            return
        if role in member.roles:
            await member.remove_roles(role, reason="Button role")
            await interaction.response.send_message(f"Removed role {role.name}", ephemeral=True)
        else:
            await member.add_roles(role, reason="Button role")
            await interaction.response.send_message(f"Added role {role.name}", ephemeral=True)
