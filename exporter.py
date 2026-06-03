import logging
from typing import Union

import discord

logger = logging.getLogger(__name__)


class ServerExporter:
    def __init__(self, guild: discord.Guild):
        self.guild = guild

    async def export(self) -> str:
        lines: list[str] = []

        lines.append('SERVER {')
        lines.append(f'    name = "{self.guild.name}"')
        lines.append('')

        roles = [
            r for r in sorted(self.guild.roles, key=lambda r: r.position, reverse=True)
            if not r.is_default() and not r.is_premium_subscriber() and not r.managed
        ]
        for role in roles:
            lines.append(self._export_role(role))
            lines.append('')

        for category in self.guild.categories:
            lines.append(self._export_category(category))
            lines.append('')

        uncategorized_channels = [
            c for c in self.guild.channels
            if c.category is None and not isinstance(c, discord.CategoryChannel)
        ]
        for channel in uncategorized_channels:
            lines.append(f'    {self._indent(self._export_channel(channel), 4)}')
            lines.append('')

        lines.append('}')
        return '\n'.join(lines).rstrip('\n') + '\n'

    def _export_role(self, role: discord.Role) -> str:
        lines: list[str] = ['    ROLE {']
        lines.append(f'        name = "{role.name}"')
        if role.color.value != 0:
            lines.append(f'        color = "#{role.color.value:06x}"')
        enabled_perms = [
            perm for perm, value in role.permissions if value
        ]
        if enabled_perms:
            lines.append(f'        permissions = {",".join(enabled_perms)}')
        if role.hoist:
            lines.append('        hoist = true')
        if role.mentionable:
            lines.append('        mentionable = true')
        lines.append('    }')
        return '\n'.join(lines)

    def _export_category(self, category: discord.CategoryChannel) -> str:
        lines: list[str] = ['    CATEGORY {']
        lines.append(f'        name = "{category.name}"')
        for channel in category.channels:
            exported = self._indent(self._export_channel(channel), 8)
            lines.append('')
            lines.append(exported)
        lines.append('    }')
        return '\n'.join(lines)

    def _export_channel(self, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.ForumChannel]) -> str:
        if isinstance(channel, discord.TextChannel):
            return self._export_text_channel(channel)
        elif isinstance(channel, discord.VoiceChannel):
            return self._export_voice_channel(channel)
        elif isinstance(channel, discord.StageChannel):
            return self._export_stage_channel(channel)
        elif isinstance(channel, discord.ForumChannel):
            return self._export_forum_channel(channel)
        return f'# Unknown channel: {channel.name}'

    def _export_text_channel(self, channel: discord.TextChannel) -> str:
        lines: list[str] = ['TEXT {']
        lines.append(f'    name = "{channel.name}"')
        if channel.topic:
            topic = channel.topic.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'    topic = "{topic}"')
        if channel.slowmode_delay > 0:
            lines.append(f'    slowmode = {channel.slowmode_delay}')
        if channel.nsfw:
            lines.append('    nsfw = true')
        overwrite = channel.overwrites_for(self.guild.default_role)
        if overwrite.send_messages is False:
            lines.append('    readonly = true')
        lines.extend(self._export_permission_overwrites(channel))
        lines.append('}')
        return '\n'.join(lines)

    def _export_voice_channel(self, channel: discord.VoiceChannel) -> str:
        lines: list[str] = ['VOICE {']
        lines.append(f'    name = "{channel.name}"')
        lines.append(f'    bitrate = {channel.bitrate}')
        if channel.user_limit > 0:
            lines.append(f'    limit = {channel.user_limit}')
        lines.extend(self._export_permission_overwrites(channel))
        lines.append('}')
        return '\n'.join(lines)

    def _export_stage_channel(self, channel: discord.StageChannel) -> str:
        lines: list[str] = ['STAGE {']
        lines.append(f'    name = "{channel.name}"')
        lines.extend(self._export_permission_overwrites(channel))
        lines.append('}')
        return '\n'.join(lines)

    def _export_forum_channel(self, channel: discord.ForumChannel) -> str:
        lines: list[str] = ['FORUM {']
        lines.append(f'    name = "{channel.name}"')
        if channel.topic:
            topic = channel.topic.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'    topic = "{topic}"')
        if channel.slowmode_delay > 0:
            lines.append(f'    slowmode = {channel.slowmode_delay}')
        if channel.nsfw:
            lines.append('    nsfw = true')
        if channel.category:
            lines.append(f'    category = "{channel.category.name}"')
        lines.extend(self._export_permission_overwrites(channel))
        lines.append('}')
        return '\n'.join(lines)

    def _export_permission_overwrites(self, channel: discord.abc.GuildChannel) -> list[str]:
        lines: list[str] = []
        allow_roles: list[str] = []
        deny_roles: list[str] = []
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Role) and not target.is_default() and not target.managed:
                if overwrite.view_channel is True:
                    allow_roles.append(target.name)
                elif overwrite.view_channel is False:
                    deny_roles.append(target.name)
        if allow_roles:
            lines.append(f'    allow = {",".join(allow_roles)}')
        if deny_roles:
            lines.append(f'    deny = {",".join(deny_roles)}')
        return lines

    @staticmethod
    def _indent(text: str, spaces: int = 4) -> str:
        indent = ' ' * spaces
        return '\n'.join(indent + line for line in text.split('\n'))
