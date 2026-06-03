import logging
from typing import Optional

import discord

from models import WelcomeModel, AutoRoleModel

logger = logging.getLogger(__name__)


class WelcomeManager:
    def __init__(self):
        self.configs: dict[int, WelcomeModel] = {}
        self.role_configs: dict[int, AutoRoleModel] = {}

    def set_welcome(self, guild_id: int, config: Optional[WelcomeModel]):
        if config:
            self.configs[guild_id] = config
        else:
            self.configs.pop(guild_id, None)

    def set_auto_role(self, guild_id: int, config: Optional[AutoRoleModel]):
        if config:
            self.role_configs[guild_id] = config
        else:
            self.role_configs.pop(guild_id, None)

    def remove_guild(self, guild_id: int):
        self.configs.pop(guild_id, None)
        self.role_configs.pop(guild_id, None)

    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        guild_id = guild.id

        role_config = self.role_configs.get(guild_id)
        if role_config:
            role = discord.utils.get(guild.roles, name=role_config.role)
            if role:
                try:
                    await member.add_roles(role, reason="Auto role")
                    logger.info(f"Added auto-role '{role.name}' to {member}")
                except Exception as e:
                    logger.error(f"Auto-role failed for {member}: {e}")

        welcome = self.configs.get(guild_id)
        if welcome and welcome.channel:
            channel = discord.utils.get(guild.text_channels, name=welcome.channel)
            if channel:
                try:
                    msg = welcome.message.replace("{user}", member.mention)
                    msg = msg.replace("{username}", member.name)
                    msg = msg.replace("{member_count}", str(guild.member_count))
                    msg = msg.replace("{server_name}", guild.name)
                    await channel.send(msg)
                except Exception as e:
                    logger.error(f"Welcome message failed: {e}")
