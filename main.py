import asyncio
import io
import logging
import os
import sys
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import TOKEN
from models import ParseError, ServerModel
from parser import Tokenizer, Parser, preprocess
from builder import ServerBuilder
from exporter import ServerExporter
from welcome import WelcomeManager
from tickets import TicketManager, TicketView, TicketCloseView
from temp_voice import TempVoiceManager
from reactions import ReactionRoleManager

logger = logging.getLogger(__name__)

TEST_GUILD_ID = None

welcome_mgr = WelcomeManager()
ticket_mgr = TicketManager()
temp_voice_mgr = TempVoiceManager()
reaction_mgr = ReactionRoleManager()


def _extract_server_model(text: str, base_dir: str) -> ServerModel:
    processed = preprocess(text, base_dir)
    tokenizer = Tokenizer(processed)
    tokens = tokenizer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.voice_states = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.add_cog(ServerCommands(self))
        self.add_view(TicketCloseView(0, ticket_mgr))

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        try:
            if TEST_GUILD_ID is not None:
                guild = discord.Object(id=TEST_GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Synced commands to guild {TEST_GUILD_ID}")
            else:
                await self.tree.sync()
                logger.info("Global sync complete")
        except Exception as e:
            logger.warning(f"Command sync failed: {e}")

    async def on_member_join(self, member: discord.Member):
        await welcome_mgr.on_member_join(member)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        await temp_voice_mgr.on_voice_state_update(member, before, after)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await reaction_mgr.on_raw_reaction_add(payload, self)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await reaction_mgr.on_raw_reaction_remove(payload, self)

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get('custom_id', '') if interaction.data else ''
            if custom_id.startswith('br_'):
                await reaction_mgr.on_button_interaction(interaction)


class ServerCommands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(name="build", description="Build Discord server from DSL template file")
    @app_commands.describe(file="Template file (.txt) with DSL config")
    async def build(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer(ephemeral=False)

        if not file.filename.endswith('.txt'):
            await interaction.followup.send("❌ Upload a `.txt` file.")
            return

        try:
            template_bytes = await file.read()
            template_text = template_bytes.decode('utf-8')
        except UnicodeDecodeError:
            await interaction.followup.send("❌ File encoding error. Use UTF-8.")
            return

        try:
            if not template_text.strip():
                await interaction.followup.send("❌ Template is empty.")
                return

            guild = interaction.guild
            if guild is None:
                await interaction.followup.send("❌ Use this in a server.")
                return

            me = guild.me
            if not me.guild_permissions.manage_guild:
                await interaction.followup.send("❌ I need **Manage Server** permission."); return
            if not me.guild_permissions.manage_roles:
                await interaction.followup.send("❌ I need **Manage Roles** permission."); return
            if not me.guild_permissions.manage_channels:
                await interaction.followup.send("❌ I need **Manage Channels** permission."); return

            model = _extract_server_model(template_text, os.getcwd())

            if not model.name:
                await interaction.followup.send("❌ Server name is required."); return

            # Run builder
            builder = ServerBuilder(guild)
            log = await builder.build(model)

            # Apply event-driven configs
            if model.welcome:
                welcome_mgr.set_welcome(guild.id, model.welcome)
            else:
                welcome_mgr.set_welcome(guild.id, None)

            if model.auto_role:
                welcome_mgr.set_auto_role(guild.id, model.auto_role)
            else:
                welcome_mgr.set_auto_role(guild.id, None)

            if model.tickets:
                ticket_mgr.set_config(guild.id, model.tickets)
                view = ticket_mgr.get_view(guild.id)
                if view and model.tickets.create_channel_name:
                    target = discord.utils.get(guild.text_channels, name=model.tickets.create_channel_name)
                    if target:
                        async for msg in target.history(limit=10):
                            if msg.author == self.bot.user:
                                await msg.delete()
                        await target.send("Click to create a ticket:", view=view)
                        self.bot.add_view(view)
            else:
                ticket_mgr.set_config(guild.id, None)

            if model.temp_voice:
                temp_voice_mgr.set_config(guild.id, model.temp_voice)
            else:
                temp_voice_mgr.set_config(guild.id, None)

            if model.reaction_roles:
                reaction_mgr.set_reaction_configs(guild.id, model.reaction_roles)
                for rr in model.reaction_roles:
                    target = discord.utils.get(guild.text_channels, name=rr.channel)
                    if target:
                        async for msg in target.history(limit=20):
                            if msg.author == self.bot.user and msg.content == rr.message:
                                await msg.clear_reactions()
                                await msg.add_reaction(rr.emoji)
                                break
                        else:
                            msg = await target.send(rr.message)
                            await msg.add_reaction(rr.emoji)
            else:
                reaction_mgr.set_reaction_configs(guild.id, [])

            if model.button_roles:
                reaction_mgr.set_button_configs(guild.id, model.button_roles)
                for br in model.button_roles:
                    target = discord.utils.get(guild.text_channels, name=br.channel)
                    if target:
                        view = reaction_mgr.get_button_view(guild.id)
                        if view:
                            async for msg in target.history(limit=10):
                                if msg.author == self.bot.user:
                                    await msg.delete()
                            await target.send("**Roles:**", view=view)
                            self.bot.add_view(view)
            else:
                reaction_mgr.set_button_configs(guild.id, [])

            # Counters: start background task
            if model.counters:
                asyncio.ensure_future(self._update_counters(guild, model))

            # Auto messages: start background task
            if model.auto_messages:
                asyncio.ensure_future(self._run_auto_messages(guild, model))

            total_channels = (
                len(model.uncategorized) + len(model.forums) +
                sum(len(c.channels) for c in model.categories)
            )
            summary = [
                f"✅ **Build complete!**",
                f"- Roles: {len(model.roles)} ({sum(1 for l in log if 'Created role' in l)} created, {sum(1 for l in log if 'Updated role' in l)} updated)",
                f"- Channels: {total_channels} ({sum(1 for l in log if 'Created channel' in l)} created, {sum(1 for l in log if 'Updated channel' in l)} updated)",
                f"- Categories: {len(model.categories)}",
            ]
            for entry in log:
                summary.append(f"• {entry}")
            log_text = '\n'.join(summary)
            if len(log_text) > 1900:
                log_text = '\n'.join(summary[:5]) + f"\n\n... +{len(log) - 5} more"
            await interaction.followup.send(log_text)

        except ParseError as e:
            await interaction.followup.send(f"❌ **Parse Error**\n```\n{e}\n```")
        except FileNotFoundError as e:
            await interaction.followup.send(f"❌ {e}")
        except discord.Forbidden:
            await interaction.followup.send("❌ Bot lacks permissions.")
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ Discord API: {e}")
        except Exception as e:
            logger.exception("Build failed")
            await interaction.followup.send(f"❌ {e}")

    async def _update_counters(self, guild: discord.Guild, model: ServerModel):
        await asyncio.sleep(5)
        for cnt in model.counters:
            try:
                ch_name = cnt.name.replace('{count}', str(getattr(guild, f'{cnt.counter_type}_count', 0)))
                existing = discord.utils.get(guild.channels, name=ch_name)
                if existing and isinstance(existing, discord.VoiceChannel):
                    val = str(getattr(guild, f'{cnt.counter_type}_count', 0))
                    new_name = cnt.name.replace('{count}', val)
                    if existing.name != new_name:
                        await existing.edit(name=new_name)
            except Exception as e:
                logger.error(f"Counter update error: {e}")

    async def _run_auto_messages(self, guild: discord.Guild, model: ServerModel):
        await asyncio.sleep(10)
        for am in model.auto_messages:
            while True:
                try:
                    await asyncio.sleep(am.interval_hours * 3600)
                    channel = discord.utils.get(guild.text_channels, name=am.channel)
                    if channel:
                        await channel.send(am.message)
                except Exception as e:
                    logger.error(f"Auto message error: {e}")

    @app_commands.command(name="export", description="Export server to DSL template")
    async def export(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        guild = interaction.guild
        if guild is None:
            await interaction.followup.send("❌ Use in a server."); return
        me = guild.me
        if not me.guild_permissions.view_channel:
            await interaction.followup.send("❌ I need View Channel."); return
        try:
            exporter = ServerExporter(guild)
            dsl_text = await exporter.export()
            safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in f"{guild.name}_template.txt")
            file = discord.File(io.BytesIO(dsl_text.encode('utf-8')), filename=safe)
            rc = len([r for r in guild.roles if not r.is_default() and not r.managed])
            cc = len(guild.channels)
            await interaction.followup.send(f"✅ **Exported!**\nRoles: {rc} | Categories: {len(guild.categories)} | Channels: {cc}", file=file)
        except Exception as e:
            logger.exception("Export failed")
            await interaction.followup.send(f"❌ {e}")

    @app_commands.command(name="sync", description="Sync commands globally (owner)")
    async def sync(self, interaction: discord.Interaction):
        if interaction.user.id != interaction.guild.owner_id if interaction.guild else False:
            await interaction.response.send_message("❌ Server owner only.", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        try:
            await self.bot.tree.sync()
            await interaction.followup.send("✅ Commands synced globally!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ {e}", ephemeral=True)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Set TOKEN in config.py"); sys.exit(1)
    bot = Bot()
    bot.run(TOKEN, log_handler=None)


if __name__ == '__main__':
    main()
