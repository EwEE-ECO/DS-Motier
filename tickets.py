import asyncio
import logging
from typing import Optional

import discord
from discord import ui

from models import TicketSettings

logger = logging.getLogger(__name__)


class TicketView(ui.View):
    def __init__(self, settings: TicketSettings, guild_id: int, manager: 'TicketManager'):
        super().__init__(timeout=None)
        self.settings = settings
        self.guild_id = guild_id
        self.manager = manager
        btn = ui.Button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id=f"ticket_create_{guild_id}")
        btn.callback = self.create_ticket
        self.add_item(btn)

    async def create_ticket(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"You already have a ticket: {existing.mention}", ephemeral=True)
            return

        cat = discord.utils.get(guild.categories, name=self.settings.category)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        for role_name in self.settings.staff_roles:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name.lower()}",
            category=cat,
            overwrites=overwrites,
            topic=f"Ticket for {interaction.user}",
        )
        self.manager.active_tickets[self.guild_id].append(channel.id)

        embed = discord.Embed(title="Support Ticket", description="Support will be with you shortly.", color=discord.Color.blue())
        close_view = TicketCloseView(self.guild_id, self.manager)
        await channel.send(embed=embed, view=close_view)
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)


class TicketCloseView(ui.View):
    def __init__(self, guild_id: int, manager: 'TicketManager'):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.manager = manager
        btn = ui.Button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒", custom_id=f"ticket_close_{guild_id}")
        btn.callback = self.close_ticket
        self.add_item(btn)

    async def close_ticket(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not channel:
            return
        await interaction.response.send_message("Closing ticket in 5 seconds...", ephemeral=True)
        await asyncio.sleep(5)
        await channel.delete()
        if channel.id in self.manager.active_tickets.get(self.guild_id, []):
            self.manager.active_tickets[self.guild_id].remove(channel.id)


class TicketManager:
    def __init__(self):
        self.configs: dict[int, TicketSettings] = {}
        self.active_tickets: dict[int, list[int]] = {}
        self._views: dict[int, TicketView] = {}

    def set_config(self, guild_id: int, config: Optional[TicketSettings]):
        if config:
            self.configs[guild_id] = config
            self.active_tickets.setdefault(guild_id, [])
        else:
            self.configs.pop(guild_id, None)
            self.active_tickets.pop(guild_id, None)

    def get_view(self, guild_id: int) -> Optional[TicketView]:
        config = self.configs.get(guild_id)
        if config:
            return TicketView(config, guild_id, self)
        return None
