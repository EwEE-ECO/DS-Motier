from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RoleModel:
    name: str = ""
    role_id: Optional[str] = None
    color: Optional[str] = None
    permissions: list[str] = field(default_factory=list)
    hoist: bool = False
    mentionable: bool = False


@dataclass
class ChannelModel:
    name: str = ""
    channel_type: str = "text"
    topic: Optional[str] = None
    slowmode: int = 0
    bitrate: Optional[int] = None
    user_limit: int = 0
    nsfw: bool = False
    readonly: bool = False
    category: Optional[str] = None
    allow_roles: list[str] = field(default_factory=list)
    deny_roles: list[str] = field(default_factory=list)
    send_messages: Optional[bool] = None
    create_threads: Optional[bool] = None
    video_quality: Optional[str] = None
    default_reaction: Optional[str] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class CategoryModel:
    name: str = ""
    channels: list[ChannelModel] = field(default_factory=list)
    allow_roles: list[str] = field(default_factory=list)
    deny_roles: list[str] = field(default_factory=list)


@dataclass
class PermissionGroupModel:
    group_id: str = ""
    roles: list[str] = field(default_factory=list)


@dataclass
class RulesChannelModel:
    name: str = ""


@dataclass
class CommunitySettings:
    enabled: bool = False
    rules_channel: Optional[str] = None
    updates_channel: Optional[str] = None


@dataclass
class WelcomeModel:
    channel: str = ""
    message: str = ""


@dataclass
class AutoRoleModel:
    role: str = ""
    role_id: Optional[str] = None


@dataclass
class ReactionRoleModel:
    channel: str = ""
    message: str = ""
    emoji: str = ""
    role: str = ""
    role_id: Optional[str] = None


@dataclass
class ButtonRoleModel:
    channel: str = ""
    label: str = ""
    role: str = ""
    role_id: Optional[str] = None
    style: str = "primary"


@dataclass
class TicketSettings:
    category: str = ""
    staff_roles: list[str] = field(default_factory=list)
    create_channel_name: str = "create-ticket"
    transcript: bool = True
    auto_close_days: int = 30


@dataclass
class TempVoiceSettings:
    name: str = "➕ Create Room"
    category: Optional[str] = None
    user_limit: int = 0


@dataclass
class LogsSettings:
    joins: Optional[str] = None
    leaves: Optional[str] = None
    message_delete: Optional[str] = None
    message_edit: Optional[str] = None
    voice_events: Optional[str] = None
    moderation: Optional[str] = None


@dataclass
class CounterModel:
    counter_type: str = "members"
    name: str = "{count}"
    channel_id: Optional[int] = None


@dataclass
class AutoMessageModel:
    channel: str = ""
    interval_hours: int = 24
    message: str = ""


@dataclass
class EmojiModel:
    name: str = ""
    file: str = ""


@dataclass
class StickerModel:
    name: str = ""
    file: str = ""


@dataclass
class WebhookModel:
    channel: str = ""
    name: str = ""


@dataclass
class ScheduledEventModel:
    name: str = ""
    description: Optional[str] = None
    date: str = ""


@dataclass
class TextTemplateModel:
    name: str = ""
    count: int = 1


@dataclass
class BotConfig:
    prefix: str = "!"
    language: str = "en"


@dataclass
class ServerModel:
    name: str = ""
    description: Optional[str] = None
    verification_level: Optional[str] = None
    default_notifications: Optional[str] = None
    roles: list[RoleModel] = field(default_factory=list)
    categories: list[CategoryModel] = field(default_factory=list)
    uncategorized: list[ChannelModel] = field(default_factory=list)
    forums: list[ChannelModel] = field(default_factory=list)
    permission_groups: list[PermissionGroupModel] = field(default_factory=list)
    rules_channel: Optional[RulesChannelModel] = None
    community: Optional[CommunitySettings] = None
    welcome: Optional[WelcomeModel] = None
    auto_role: Optional[AutoRoleModel] = None
    reaction_roles: list[ReactionRoleModel] = field(default_factory=list)
    button_roles: list[ButtonRoleModel] = field(default_factory=list)
    tickets: Optional[TicketSettings] = None
    temp_voice: Optional[TempVoiceSettings] = None
    logs: Optional[LogsSettings] = None
    counters: list[CounterModel] = field(default_factory=list)
    auto_messages: list[AutoMessageModel] = field(default_factory=list)
    emojis: list[EmojiModel] = field(default_factory=list)
    stickers: list[StickerModel] = field(default_factory=list)
    webhooks: list[WebhookModel] = field(default_factory=list)
    scheduled_events: list[ScheduledEventModel] = field(default_factory=list)
    text_templates: list[TextTemplateModel] = field(default_factory=list)
    bot_config: Optional[BotConfig] = None


class ParseError(Exception):
    def __init__(self, line: int, column: int, message: str):
        self.line = line
        self.column = column
        self.message = message
        super().__init__(str(self))

    def __str__(self) -> str:
        return f"Line {self.line}, Column {self.column}: {self.message}"
