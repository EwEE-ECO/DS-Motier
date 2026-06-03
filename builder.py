import asyncio
import logging
import os
from typing import Optional

import discord

from config import PERMISSION_MAP, NAMED_COLORS
from models import (
    ServerModel, RoleModel, ChannelModel, CategoryModel,
    PermissionGroupModel, RulesChannelModel, CommunitySettings,
    TempVoiceSettings, LogsSettings, CounterModel, AutoMessageModel,
    EmojiModel, StickerModel, WebhookModel, ScheduledEventModel,
    TextTemplateModel, BotConfig,
)

logger = logging.getLogger(__name__)

READONLY_DENIED = {
    "send_messages": False,
    "add_reactions": False,
    "create_public_threads": False,
    "create_private_threads": False,
    "send_messages_in_threads": False,
}


class ServerBuilder:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.log: list[str] = []
        self._role_cache: dict[str, discord.Role] = {}
        self._channel_cache: dict[str, discord.abc.GuildChannel] = {}

    async def build(self, model: ServerModel) -> list[str]:
        self.log = []
        self._role_cache = {r.name: r for r in self.guild.roles if not r.managed}
        self._channel_cache = {c.name: c for c in self.guild.channels}

        await self._apply_server_settings(model)
        await self._build_roles(model.roles)
        await self._build_permission_groups(model.permission_groups)

        category_map = await self._build_categories(model.categories)

        for ch_model in model.uncategorized:
            cat = category_map.get(ch_model.category) if ch_model.category else None
            await self._create_or_update_channel(ch_model, cat)

        for forum_model in model.forums:
            cat = category_map.get(forum_model.category) if forum_model.category else None
            await self._create_or_update_channel(forum_model, cat)

        if model.rules_channel:
            await self._setup_rules_channel(model.rules_channel)

        if model.community and model.community.enabled:
            await self._setup_community(model.community)

        await self._build_emojis(model.emojis)
        await self._build_stickers(model.stickers)
        await self._build_webhooks(model.webhooks, category_map)
        await self._build_scheduled_events(model.scheduled_events)
        await self._build_counters(model.counters)
        await self._build_text_templates(model.text_templates, category_map)

        return self.log

    async def _apply_server_settings(self, model: ServerModel):
        kwargs = {}
        if model.name:
            kwargs['name'] = model.name
        if model.description is not None:
            kwargs['description'] = model.description
        if model.verification_level:
            vmap = {'none': discord.VerificationLevel.none, 'low': discord.VerificationLevel.low,
                    'medium': discord.VerificationLevel.medium, 'high': discord.VerificationLevel.high,
                    'highest': discord.VerificationLevel.highest}
            if model.verification_level in vmap:
                kwargs['verification_level'] = vmap[model.verification_level]
        if model.default_notifications:
            nmap = {'all': discord.NotificationLevel.all_messages, 'mentions': discord.NotificationLevel.only_mentions}
            if model.default_notifications in nmap:
                kwargs['default_notifications'] = nmap[model.default_notifications]
        if kwargs:
            await self.guild.edit(**kwargs)
            self.log.append(f"Updated server settings: {', '.join(kwargs.keys())}")

    async def _build_roles(self, roles: list[RoleModel]):
        existing = {r.name: r for r in self.guild.roles if not r.is_default() and not r.is_premium_subscriber() and not r.managed}
        for rm in roles:
            if rm.name in existing:
                role = existing[rm.name]
                await self._update_role(role, rm)
                self.log.append(f"Updated role '{rm.name}'")
            else:
                role = await self._create_role(rm)
                self.log.append(f"Created role '{rm.name}'")
            self._role_cache[rm.name] = role
            if rm.role_id:
                self._role_cache[rm.role_id] = role

    async def _update_role(self, role: discord.Role, model: RoleModel):
        kwargs = {}
        if model.color is not None:
            kwargs['color'] = self._parse_color(model.color)
        if model.permissions:
            kwargs['permissions'] = self._parse_permissions(model.permissions)
        if model.hoist:
            kwargs['hoist'] = True
        if model.mentionable:
            kwargs['mentionable'] = True
        if kwargs:
            await role.edit(**kwargs)

    async def _create_role(self, model: RoleModel) -> discord.Role:
        color = self._parse_color(model.color) if model.color else discord.Color.default()
        perms = self._parse_permissions(model.permissions) if model.permissions else discord.Permissions.none()
        return await self.guild.create_role(name=model.name, color=color, permissions=perms, hoist=model.hoist, mentionable=model.mentionable)

    def _parse_color(self, color_str: str) -> discord.Color:
        if color_str.startswith('#'):
            return discord.Color(int(color_str[1:], 16))
        hex_val = NAMED_COLORS.get(color_str.lower())
        if hex_val is not None:
            return discord.Color(hex_val)
        try:
            return discord.Color(int(color_str, 16))
        except (ValueError, TypeError):
            return discord.Color.default()

    def _parse_permissions(self, perms: list[str]) -> discord.Permissions:
        p = discord.Permissions.none()
        for perm in perms:
            attr = PERMISSION_MAP.get(perm.lower())
            if attr:
                setattr(p, attr, True)
        return p

    async def _build_permission_groups(self, groups: list[PermissionGroupModel]):
        pass

    async def _build_categories(self, categories: list[CategoryModel]) -> dict[str, discord.CategoryChannel]:
        existing = {c.name: c for c in self.guild.categories}
        cat_map: dict[str, discord.CategoryChannel] = {}
        for cm in categories:
            if cm.name in existing:
                cat = existing[cm.name]
                self.log.append(f"Category '{cm.name}' already exists")
            else:
                overwrites = self._build_overwrites_raw(cm.allow_roles, cm.deny_roles)
                kwargs = {'name': cm.name}
                if overwrites:
                    kwargs['overwrites'] = overwrites
                cat = await self.guild.create_category(**kwargs)
                self.log.append(f"Created category '{cm.name}'")
            cat_map[cm.name] = cat
            for chm in cm.channels:
                await self._create_or_update_channel(chm, cat)
        return cat_map

    async def _create_or_update_channel(self, model: ChannelModel, category: Optional[discord.CategoryChannel] = None):
        existing = None
        for ch in self.guild.channels:
            if ch.name == model.name:
                if category is None and ch.category is None:
                    existing = ch; break
                elif category is not None and ch.category is not None and ch.category.id == category.id:
                    existing = ch; break
        if existing:
            await self._update_channel(existing, model, category)
            self.log.append(f"Updated channel '{model.name}'")
            self._channel_cache[model.name] = existing
        else:
            ch = await self._create_channel(model, category)
            if ch:
                self.log.append(f"Created channel '{model.name}'")
                self._channel_cache[model.name] = ch

    async def _create_channel(self, model: ChannelModel, category: Optional[discord.CategoryChannel] = None) -> Optional[discord.abc.GuildChannel]:
        kwargs = {'name': model.name}
        if category:
            kwargs['category'] = category
        overwrites = self._build_overwrites(model, model.channel_type)

        try:
            if model.channel_type == 'text':
                kwargs['topic'] = model.topic or ""
                kwargs['slowmode_delay'] = model.slowmode
                kwargs['nsfw'] = model.nsfw
                if model.send_messages is not None:
                    if overwrites is None:
                        overwrites = {}
                    overwrites[self.guild.default_role] = discord.PermissionOverwrite(
                        send_messages=model.send_messages
                    )
                if model.create_threads is not None:
                    if overwrites is None:
                        overwrites = {}
                    target = overwrites.get(self.guild.default_role, discord.PermissionOverwrite())
                    target.create_public_threads = model.create_threads
                    target.create_private_threads = model.create_threads
                    overwrites[self.guild.default_role] = target
                if overwrites:
                    kwargs['overwrites'] = overwrites
                return await self.guild.create_text_channel(**kwargs)

            elif model.channel_type == 'voice':
                kwargs['bitrate'] = model.bitrate or 64000
                kwargs['user_limit'] = model.user_limit
                if overwrites:
                    kwargs['overwrites'] = overwrites
                return await self.guild.create_voice_channel(**kwargs)

            elif model.channel_type == 'stage':
                if overwrites:
                    kwargs['overwrites'] = overwrites
                return await self.guild.create_stage_channel(**kwargs)

            elif model.channel_type == 'forum':
                kwargs['topic'] = model.topic or ""
                kwargs['slowmode_delay'] = model.slowmode
                kwargs['nsfw'] = model.nsfw
                kwargs['default_thread_slowmode_delay'] = model.slowmode
                if model.tags:
                    kwargs['available_tags'] = [discord.ForumTag(name=t, moderated=False) for t in model.tags]
                if model.default_reaction:
                    kwargs['default_reaction_emoji'] = model.default_reaction
                if overwrites:
                    kwargs['overwrites'] = overwrites
                return await self.guild.create_forum(**kwargs)

            raise ValueError(f"Unknown channel type: {model.channel_type}")
        except discord.HTTPException as e:
            self.log.append(f"Skipped '{model.name}': {e}")
            return None

    def _build_overwrites(self, model: ChannelModel, channel_type: str = "text") -> Optional[dict]:
        overwrites = {}
        if model.readonly and channel_type in ("text", "forum"):
            overwrites[self.guild.default_role] = discord.PermissionOverwrite(**READONLY_DENIED)
        role_map = self._role_cache
        for rn in model.allow_roles:
            role = role_map.get(rn)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True)
        for rn in model.deny_roles:
            role = role_map.get(rn)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=False)
        return overwrites if overwrites else None

    def _build_overwrites_raw(self, allow: list[str], deny: list[str]) -> Optional[dict]:
        overwrites = {}
        for rn in allow:
            role = self._role_cache.get(rn)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True)
        for rn in deny:
            role = self._role_cache.get(rn)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=False)
        return overwrites if overwrites else None

    async def _update_channel(self, channel: discord.abc.GuildChannel, model: ChannelModel, category: Optional[discord.CategoryChannel] = None):
        kwargs = {}
        if isinstance(channel, discord.TextChannel):
            if model.topic is not None and channel.topic != model.topic:
                kwargs['topic'] = model.topic
            if model.slowmode != channel.slowmode_delay:
                kwargs['slowmode_delay'] = model.slowmode
            if model.nsfw != channel.nsfw:
                kwargs['nsfw'] = model.nsfw
        elif isinstance(channel, discord.VoiceChannel):
            if model.bitrate is not None and model.bitrate != channel.bitrate:
                kwargs['bitrate'] = model.bitrate
            if model.user_limit != channel.user_limit:
                kwargs['user_limit'] = model.user_limit
        elif isinstance(channel, discord.ForumChannel):
            if model.topic is not None and channel.topic != model.topic:
                kwargs['topic'] = model.topic
            if model.slowmode != channel.slowmode_delay:
                kwargs['slowmode_delay'] = model.slowmode
            if model.nsfw != channel.nsfw:
                kwargs['nsfw'] = model.nsfw
        if model.name != channel.name:
            kwargs['name'] = model.name
        if category is not None and channel.category != category:
            kwargs['category'] = category
        if kwargs:
            await channel.edit(**kwargs)
        await self._apply_channel_overwrites(channel, model)

    async def _apply_channel_overwrites(self, channel: discord.abc.GuildChannel, model: ChannelModel):
        if model.readonly and isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
            ow = channel.overwrites_for(self.guild.default_role)
            needs = any(getattr(ow, p) is not v for p, v in READONLY_DENIED.items())
            if needs:
                for p, v in READONLY_DENIED.items():
                    setattr(ow, p, v)
                await channel.set_permissions(self.guild.default_role, overwrite=ow)
                self.log.append(f"Applied read-only to '{channel.name}'")
        for rn in model.allow_roles:
            role = self._role_cache.get(rn)
            if role:
                existing = channel.overwrites_for(role)
                if existing.view_channel is not True:
                    await channel.set_permissions(role, overwrite=discord.PermissionOverwrite(view_channel=True))
                    self.log.append(f"Allowed '{rn}' to view '{channel.name}'")
        for rn in model.deny_roles:
            role = self._role_cache.get(rn)
            if role:
                existing = channel.overwrites_for(role)
                if existing.view_channel is not False:
                    await channel.set_permissions(role, overwrite=discord.PermissionOverwrite(view_channel=False))
                    self.log.append(f"Denied '{rn}' access to '{channel.name}'")

    async def _setup_rules_channel(self, rules: RulesChannelModel):
        for ch in self.guild.text_channels:
            if ch.name == rules.name:
                try:
                    await self.guild.edit(rules_channel=ch)
                    self.log.append(f"Set '{rules.name}' as rules channel")
                except Exception as e:
                    self.log.append(f"Could not set rules channel: {e}")
                break

    async def _setup_community(self, community: CommunitySettings):
        try:
            rules = None
            updates = None
            for ch in self.guild.text_channels:
                if community.rules_channel and ch.name == community.rules_channel:
                    rules = ch
                if community.updates_channel and ch.name == community.updates_channel:
                    updates = ch
            if rules or updates:
                kwargs = {}
                if rules:
                    kwargs['rules_channel'] = rules
                if updates:
                    kwargs['public_updates_channel'] = updates
                await self.guild.edit(**kwargs)
                self.log.append("Community settings applied")
        except Exception as e:
            self.log.append(f"Community setup note: {e}")

    async def _build_emojis(self, emojis: list[EmojiModel]):
        for em in emojis:
            if not os.path.exists(em.file):
                self.log.append(f"Emoji file not found: {em.file}")
                continue
            try:
                with open(em.file, 'rb') as f:
                    await self.guild.create_custom_emoji(name=em.name, image=f.read())
                self.log.append(f"Created emoji '{em.name}'")
            except Exception as e:
                self.log.append(f"Failed to create emoji '{em.name}': {e}")

    async def _build_stickers(self, stickers: list[StickerModel]):
        for st in stickers:
            if not os.path.exists(st.file):
                self.log.append(f"Sticker file not found: {st.file}")
                continue
            try:
                with open(st.file, 'rb') as f:
                    await self.guild.create_sticker(name=st.name, file=f.read(), emoji='👍')
                self.log.append(f"Created sticker '{st.name}'")
            except Exception as e:
                self.log.append(f"Failed to create sticker '{st.name}': {e}")

    async def _build_webhooks(self, webhooks: list[WebhookModel], category_map: dict):
        for wh in webhooks:
            target = self._channel_cache.get(wh.channel)
            if target and isinstance(target, discord.TextChannel):
                try:
                    await target.create_webhook(name=wh.name)
                    self.log.append(f"Created webhook '{wh.name}' in '{wh.channel}'")
                except Exception as e:
                    self.log.append(f"Failed to create webhook: {e}")

    async def _build_scheduled_events(self, events: list[ScheduledEventModel]):
        for ev in events:
            try:
                from datetime import datetime
                start = datetime.strptime(ev.date, '%Y-%m-%d') if ev.date else datetime.now()
                await self.guild.create_scheduled_event(
                    name=ev.name, description=ev.description or "",
                    start_time=start, end_time=start,
                    entity_type=discord.EntityType.external,
                    location="Discord"
                )
                self.log.append(f"Created event '{ev.name}'")
            except Exception as e:
                self.log.append(f"Failed to create event '{ev.name}': {e}")

    async def _build_counters(self, counters: list[CounterModel]):
        for cnt in counters:
            name = cnt.name.replace('{count}', '0')
            try:
                existing = discord.utils.get(self.guild.channels, name=name)
                if not existing:
                    await self.guild.create_voice_channel(name=name)
                    self.log.append(f"Created counter channel '{name}'")
            except Exception as e:
                self.log.append(f"Failed to create counter '{name}': {e}")

    async def _build_text_templates(self, templates: list[TextTemplateModel], category_map: dict):
        for tmpl in templates:
            for i in range(1, (getattr(tmpl, 'count', 1) or 1) + 1):
                ch_name = tmpl.name.replace('{number}', str(i))
                existing = discord.utils.get(self.guild.channels, name=ch_name)
                if not existing:
                    try:
                        await self.guild.create_text_channel(name=ch_name)
                        self.log.append(f"Created templated channel '{ch_name}'")
                    except Exception as e:
                        self.log.append(f"Failed to create '{ch_name}': {e}")
