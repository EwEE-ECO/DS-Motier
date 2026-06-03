import logging
from typing import Optional

import discord

from models import TempVoiceSettings

logger = logging.getLogger(__name__)


class TempVoiceManager:
    def __init__(self):
        self.configs: dict[int, TempVoiceSettings] = {}
        self.temp_channels: dict[int, set[int]] = {}

    def set_config(self, guild_id: int, config: Optional[TempVoiceSettings]):
        if config:
            self.configs[guild_id] = config
            self.temp_channels.setdefault(guild_id, set())
        else:
            self.configs.pop(guild_id, None)
            self.temp_channels.pop(guild_id, None)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild
        config = self.configs.get(guild.id)
        if not config:
            return

        if after.channel and config.name and after.channel.name == config.name:
            cat = None
            if config.category:
                cat = discord.utils.get(guild.categories, name=config.category)
            new_channel = await guild.create_voice_channel(
                name=f"{member.display_name}'s Room",
                category=cat,
                user_limit=config.user_limit or 0,
            )
            await member.move_to(new_channel)
            self.temp_channels.setdefault(guild.id, set()).add(new_channel.id)

        if before.channel and before.channel.id in self.temp_channels.get(guild.id, set()):
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                    self.temp_channels[guild.id].discard(before.channel.id)
                except Exception as e:
                    logger.error(f"Failed to delete temp channel: {e}")
