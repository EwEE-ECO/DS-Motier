import os
from typing import Optional

from models import (
    ServerModel, RoleModel, CategoryModel, ChannelModel, ParseError,
    PermissionGroupModel, RulesChannelModel, CommunitySettings,
    WelcomeModel, AutoRoleModel, ReactionRoleModel, ButtonRoleModel,
    TicketSettings, TempVoiceSettings, LogsSettings, CounterModel,
    AutoMessageModel, EmojiModel, StickerModel, WebhookModel,
    ScheduledEventModel, TextTemplateModel, BotConfig,
)


class TokenType:
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    EQUALS = "EQUALS"
    COMMA = "COMMA"
    STRING = "STRING"
    NUMBER = "NUMBER"
    COLOR = "COLOR"
    IDENTIFIER = "IDENTIFIER"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


class Token:
    def __init__(self, type: str, value: str, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"Token({self.type}, '{self.value}', L{self.line}:C{self.column})"


class Tokenizer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1

    def advance(self):
        if self.pos < len(self.text):
            if self.text[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def peek_char(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        if idx < len(self.text):
            return self.text[idx]
        return None

    def skip_line(self):
        while self.pos < len(self.text) and self.text[self.pos] != '\n':
            self.advance()

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []

        if len(self.text) > 0 and self.text[self.pos] == '\ufeff':
            self.advance()

        while self.pos < len(self.text):
            c = self.text[self.pos]

            if c in (' ', '\t', '\r'):
                self.advance()
                continue

            if c == '\n':
                tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                self.advance()
                continue

            if c == '/' and self.peek_char(1) == '/':
                self.skip_line()
                continue

            if c == '{':
                tokens.append(Token(TokenType.LBRACE, '{', self.line, self.column))
                self.advance()
                continue

            if c == '}':
                tokens.append(Token(TokenType.RBRACE, '}', self.line, self.column))
                self.advance()
                continue

            if c == '=':
                tokens.append(Token(TokenType.EQUALS, '=', self.line, self.column))
                self.advance()
                continue

            if c == ',':
                tokens.append(Token(TokenType.COMMA, ',', self.line, self.column))
                self.advance()
                continue

            if c == '"':
                self._tokenize_string(tokens)
                continue

            if c == '#':
                self._tokenize_color(tokens)
                continue

            if c.isdigit():
                self._tokenize_number(tokens)
                continue

            if c.isalpha() or c == '_':
                self._tokenize_identifier(tokens)
                continue

            raise ParseError(self.line, self.column, f"Unexpected character: '{c}'")

        tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return tokens

    def _tokenize_string(self, tokens: list[Token]):
        start_line = self.line
        start_col = self.column
        self.advance()
        value: list[str] = []

        while self.pos < len(self.text):
            c = self.text[self.pos]
            if c == '\\' and self.peek_char(1) in ('"', '\\', 'n', 't', 'r'):
                self.advance()
                esc = self.text[self.pos]
                if esc == 'n': value.append('\n')
                elif esc == 't': value.append('\t')
                elif esc == 'r': value.append('\r')
                elif esc == '"': value.append('"')
                elif esc == '\\': value.append('\\')
                self.advance()
            elif c == '"':
                self.advance()
                tokens.append(Token(TokenType.STRING, ''.join(value), start_line, start_col))
                return
            elif c == '\n':
                raise ParseError(self.line, self.column, "Unterminated string (newline before closing quote)")
            else:
                value.append(c)
                self.advance()

        raise ParseError(start_line, start_col, "Unterminated string (reached end of file)")

    def _tokenize_color(self, tokens: list[Token]):
        start_line = self.line
        start_col = self.column
        chars: list[str] = ['#']
        self.advance()
        while len(chars) < 7 and self.pos < len(self.text) and self.text[self.pos] in '0123456789abcdefABCDEF':
            chars.append(self.text[self.pos])
            self.advance()
        value = ''.join(chars)
        if len(value) != 7:
            raise ParseError(start_line, start_col, f"Invalid color code '{value}'. Expected: #RRGGBB")
        tokens.append(Token(TokenType.COLOR, value, start_line, start_col))

    def _tokenize_number(self, tokens: list[Token]):
        start_line = self.line
        start_col = self.column
        value: list[str] = []
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            value.append(self.text[self.pos])
            self.advance()
        tokens.append(Token(TokenType.NUMBER, ''.join(value), start_line, start_col))

    def _tokenize_identifier(self, tokens: list[Token]):
        start_line = self.line
        start_col = self.column
        value: list[str] = []
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in ('_', '-')):
            value.append(self.text[self.pos])
            self.advance()
        tokens.append(Token(TokenType.IDENTIFIER, ''.join(value), start_line, start_col))


def preprocess(text: str, base_dir: str = ".", visited: Optional[set] = None) -> str:
    if visited is None:
        visited = set()
    lines = text.split('\n')
    result_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('INCLUDE '):
            rest = stripped[8:].strip()
            if not (rest.startswith('"') and rest.endswith('"')):
                raise ParseError(0, 0, f"Invalid INCLUDE: {stripped}. Expected INCLUDE \"filename\"")
            filename = rest[1:-1]
            filepath = os.path.join(base_dir, filename)
            abs_path = os.path.abspath(filepath)
            if abs_path in visited:
                raise ParseError(0, 0, f"Circular INCLUDE: {filename}")
            visited.add(abs_path)
            if not os.path.exists(filepath):
                raise ParseError(0, 0, f"File not found: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                included = f.read()
            included_resolved = preprocess(included, os.path.dirname(filepath), visited)
            result_lines.append(included_resolved)
        else:
            result_lines.append(line)
    return '\n'.join(result_lines)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.variables: dict[str, str] = {}

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def consume(self, type: Optional[str] = None, value: Optional[str] = None) -> Token:
        token = self.peek()
        if type is not None and token.type != type:
            raise ParseError(token.line, token.column, f"Expected {type}, got {token.type} ('{token.value}')")
        if value is not None and token.value != value:
            raise ParseError(token.line, token.column, f"Expected '{value}', got '{token.value}'")
        self.pos += 1
        return token

    def skip_newlines(self):
        while self.pos < len(self.tokens) and self.peek().type == TokenType.NEWLINE:
            self.pos += 1

    def lookahead_non_newline(self) -> Optional[Token]:
        i = self.pos + 1
        while i < len(self.tokens) and self.tokens[i].type == TokenType.NEWLINE:
            i += 1
        return self.tokens[i] if i < len(self.tokens) else None

    def parse(self) -> ServerModel:
        self.skip_newlines()
        while self.peek().type != TokenType.EOF:
            token = self.peek()
            if token.type == TokenType.IDENTIFIER:
                if token.value == 'VAR':
                    self.parse_var_decl()
                elif token.value == 'SERVER':
                    return self.parse_server_block()
                else:
                    raise ParseError(token.line, token.column, f"Unexpected top-level: '{token.value}'")
            else:
                raise ParseError(token.line, token.column, f"Unexpected token: '{token.value}'")
            self.skip_newlines()
        return ServerModel()

    def parse_var_decl(self):
        self.consume(value='VAR')
        name_token = self.consume(type=TokenType.IDENTIFIER)
        self.consume(type=TokenType.EQUALS)
        value_token = self.consume(type=TokenType.STRING)
        self.variables[name_token.value] = value_token.value
        if self.peek().type == TokenType.NEWLINE:
            self.pos += 1

    def parse_server_block(self) -> ServerModel:
        server = ServerModel()
        self.consume(value='SERVER')
        self.consume(type=TokenType.LBRACE)
        self.skip_newlines()

        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE:
                break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER:
                raise ParseError(token.line, token.column, f"Unexpected in SERVER: '{token.value}'")

            keyword = token.value
            next_tok = self.lookahead_non_newline()
            is_block = next_tok is not None and next_tok.type == TokenType.LBRACE

            if keyword in ('ROLE', 'CATEGORY', 'TEXT', 'VOICE', 'STAGE', 'FORUM',
                           'RULES_CHANNEL', 'COMMUNITY', 'WELCOME', 'AUTO_ROLE',
                           'REACTION_ROLE', 'BUTTON_ROLE', 'TICKETS', 'TEMP_VOICE',
                           'LOGS', 'COUNTER', 'AUTO_MESSAGE', 'EMOJI', 'STICKER',
                           'WEBHOOK', 'SCHEDULED_EVENT', 'TEXT_TEMPLATE',
                           'PERMISSION_GROUP', 'BOT') and is_block:
                self.pos += 1
                self._parse_server_block_by_keyword(keyword, server)
            else:
                self._parse_server_property(server)

            self.skip_newlines()

        if self.peek().type == TokenType.EOF:
            raise ParseError(self.tokens[-1].line, self.tokens[-1].column, "Unterminated SERVER: expected '}'")
        self.consume(type=TokenType.RBRACE)
        return server

    def _parse_server_block_by_keyword(self, keyword: str, server: ServerModel):
        m = {
            'ROLE': lambda: server.roles.append(self.parse_role_block()),
            'CATEGORY': lambda: server.categories.append(self.parse_category_block()),
            'TEXT': lambda: server.uncategorized.append(self.parse_channel_block("text")),
            'VOICE': lambda: server.uncategorized.append(self.parse_channel_block("voice")),
            'STAGE': lambda: server.uncategorized.append(self.parse_channel_block("stage")),
            'FORUM': lambda: server.forums.append(self.parse_channel_block("forum")),
            'RULES_CHANNEL': lambda: setattr(server, 'rules_channel', self.parse_rules_channel_block()),
            'COMMUNITY': lambda: setattr(server, 'community', self.parse_community_block()),
            'WELCOME': lambda: setattr(server, 'welcome', self.parse_welcome_block()),
            'AUTO_ROLE': lambda: setattr(server, 'auto_role', self.parse_auto_role_block()),
            'REACTION_ROLE': lambda: server.reaction_roles.append(self.parse_reaction_role_block()),
            'BUTTON_ROLE': lambda: server.button_roles.append(self.parse_button_role_block()),
            'TICKETS': lambda: setattr(server, 'tickets', self.parse_tickets_block()),
            'TEMP_VOICE': lambda: setattr(server, 'temp_voice', self.parse_temp_voice_block()),
            'LOGS': lambda: setattr(server, 'logs', self.parse_logs_block()),
            'COUNTER': lambda: server.counters.append(self.parse_counter_block()),
            'AUTO_MESSAGE': lambda: server.auto_messages.append(self.parse_auto_message_block()),
            'EMOJI': lambda: server.emojis.append(self.parse_emoji_block()),
            'STICKER': lambda: server.stickers.append(self.parse_sticker_block()),
            'WEBHOOK': lambda: server.webhooks.append(self.parse_webhook_block()),
            'SCHEDULED_EVENT': lambda: server.scheduled_events.append(self.parse_scheduled_event_block()),
            'TEXT_TEMPLATE': lambda: server.text_templates.append(self.parse_text_template_block()),
            'PERMISSION_GROUP': lambda: server.permission_groups.append(self.parse_permission_group_block()),
            'BOT': lambda: setattr(server, 'bot_config', self.parse_bot_block()),
        }
        handler = m.get(keyword)
        if handler:
            handler()

    def _parse_server_property(self, server: ServerModel):
        name_token = self.consume(type=TokenType.IDENTIFIER)
        self.consume(type=TokenType.EQUALS)
        val = name_token.value
        if val == 'name':
            server.name = self.parse_string_value()
        elif val == 'description':
            server.description = self.parse_string_value()
        elif val == 'verification_level':
            server.verification_level = self.parse_identifier_value()
        elif val == 'default_notifications':
            server.default_notifications = self.parse_identifier_value()
        else:
            self.parse_string_value()

    # ── Role ──
    def parse_role_block(self) -> RoleModel:
        role = RoleModel()
        self.consume(type=TokenType.LBRACE)
        self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER:
                raise ParseError(token.line, token.column, f"Unexpected in ROLE: '{token.value}'")
            name = token.value
            self.pos += 1
            self.consume(type=TokenType.EQUALS)
            if name == 'name': role.name = self.parse_string_value()
            elif name == 'id': role.role_id = self.parse_identifier_value()
            elif name == 'color': role.color = self.parse_color_value()
            elif name == 'permissions': role.permissions = self.parse_identifier_list()
            elif name == 'hoist': role.hoist = self.parse_bool_value()
            elif name == 'mentionable': role.mentionable = self.parse_bool_value()
            else: raise ParseError(token.line, token.column, f"Unknown ROLE property: '{name}'")
            self.skip_newlines()
        if self.peek().type == TokenType.EOF:
            raise ParseError(self.tokens[-1].line, self.tokens[-1].column, "Unterminated ROLE: expected '}'")
        self.consume(type=TokenType.RBRACE)
        return role

    # ── Category ──
    def parse_category_block(self) -> CategoryModel:
        cat = CategoryModel()
        self.consume(type=TokenType.LBRACE)
        self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER:
                raise ParseError(token.line, token.column, f"Unexpected in CATEGORY: '{token.value}'")
            keyword = token.value
            next_tok = self.lookahead_non_newline()
            is_block = next_tok is not None and next_tok.type == TokenType.LBRACE
            if is_block:
                self.pos += 1
                if keyword == 'TEXT': cat.channels.append(self.parse_channel_block("text"))
                elif keyword == 'VOICE': cat.channels.append(self.parse_channel_block("voice"))
                elif keyword == 'STAGE': cat.channels.append(self.parse_channel_block("stage"))
                elif keyword == 'FORUM': cat.channels.append(self.parse_channel_block("forum"))
                else: raise ParseError(token.line, token.column, f"Unexpected block in CATEGORY: '{keyword}'")
            else:
                self.pos += 1
                self.consume(type=TokenType.EQUALS)
                if keyword == 'name': cat.name = self.parse_string_value()
                elif keyword == 'allow': cat.allow_roles = self.parse_role_name_list()
                elif keyword == 'deny': cat.deny_roles = self.parse_role_name_list()
                else: self.parse_string_value()
            self.skip_newlines()
        if self.peek().type == TokenType.EOF:
            raise ParseError(self.tokens[-1].line, self.tokens[-1].column, "Unterminated CATEGORY: expected '}'")
        self.consume(type=TokenType.RBRACE)
        return cat

    # ── Channel ──
    def parse_channel_block(self, channel_type: str) -> ChannelModel:
        ch = ChannelModel(channel_type=channel_type)
        self.consume(type=TokenType.LBRACE)
        self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER:
                raise ParseError(token.line, token.column, f"Unexpected in {channel_type.upper()}: '{token.value}'")
            name = token.value
            self.pos += 1
            self.consume(type=TokenType.EQUALS)
            if name == 'name': ch.name = self.parse_string_value()
            elif name == 'topic': ch.topic = self.parse_string_value()
            elif name == 'slowmode': ch.slowmode = self.parse_int_value()
            elif name == 'bitrate': ch.bitrate = self.parse_int_value()
            elif name == 'limit': ch.user_limit = self.parse_int_value()
            elif name == 'nsfw': ch.nsfw = self.parse_bool_value()
            elif name == 'readonly': ch.readonly = self.parse_bool_value()
            elif name == 'category': ch.category = self.parse_string_value()
            elif name == 'allow': ch.allow_roles = self.parse_role_name_list()
            elif name == 'deny': ch.deny_roles = self.parse_role_name_list()
            elif name == 'send_messages': ch.send_messages = self.parse_bool_value()
            elif name == 'create_threads': ch.create_threads = self.parse_bool_value()
            elif name == 'video_quality': ch.video_quality = self.parse_identifier_value()
            elif name == 'default_reaction': ch.default_reaction = self.parse_string_value()
            elif name == 'tags': ch.tags = self.parse_role_name_list()
            else: raise ParseError(token.line, token.column, f"Unknown {channel_type.upper()} property: '{name}'")
            self.skip_newlines()
        if self.peek().type == TokenType.EOF:
            raise ParseError(self.tokens[-1].line, self.tokens[-1].column, f"Unterminated {channel_type.upper()}: expected '}}'")
        self.consume(type=TokenType.RBRACE)
        return ch

    # ── New blocks ──
    def parse_rules_channel_block(self) -> RulesChannelModel:
        m = RulesChannelModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in RULES_CHANNEL: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'name': m.name = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_community_block(self) -> CommunitySettings:
        m = CommunitySettings(enabled=True)
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in COMMUNITY: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'enabled': m.enabled = self.parse_bool_value()
            elif k == 'rules_channel': m.rules_channel = self.parse_string_value()
            elif k == 'updates_channel': m.updates_channel = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_welcome_block(self) -> WelcomeModel:
        m = WelcomeModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in WELCOME: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'channel': m.channel = self.parse_string_value()
            elif k == 'message': m.message = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_auto_role_block(self) -> AutoRoleModel:
        m = AutoRoleModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in AUTO_ROLE: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'role': m.role = self.parse_role_name()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_reaction_role_block(self) -> ReactionRoleModel:
        m = ReactionRoleModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in REACTION_ROLE: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'channel': m.channel = self.parse_string_value()
            elif k == 'message': m.message = self.parse_string_value()
            elif k == 'emoji': m.emoji = self.parse_string_value()
            elif k == 'role': m.role = self.parse_role_name()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_button_role_block(self) -> ButtonRoleModel:
        m = ButtonRoleModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in BUTTON_ROLE: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'channel': m.channel = self.parse_string_value()
            elif k == 'label': m.label = self.parse_string_value()
            elif k == 'role': m.role = self.parse_role_name()
            elif k == 'style': m.style = self.parse_identifier_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_tickets_block(self) -> TicketSettings:
        m = TicketSettings()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in TICKETS: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'category': m.category = self.parse_string_value()
            elif k == 'staff_roles': m.staff_roles = self.parse_role_name_list()
            elif k == 'create_channel_name': m.create_channel_name = self.parse_string_value()
            elif k == 'transcript': m.transcript = self.parse_bool_value()
            elif k == 'auto_close_days': m.auto_close_days = self.parse_int_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_temp_voice_block(self) -> TempVoiceSettings:
        m = TempVoiceSettings()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in TEMP_VOICE: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'name': m.name = self.parse_string_value()
            elif k == 'category': m.category = self.parse_string_value()
            elif k == 'user_limit': m.user_limit = self.parse_int_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_logs_block(self) -> LogsSettings:
        m = LogsSettings()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in LOGS: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'joins': m.joins = self.parse_string_value()
            elif k == 'leaves': m.leaves = self.parse_string_value()
            elif k == 'message_delete': m.message_delete = self.parse_string_value()
            elif k == 'message_edit': m.message_edit = self.parse_string_value()
            elif k == 'voice_events': m.voice_events = self.parse_string_value()
            elif k == 'moderation': m.moderation = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_counter_block(self) -> CounterModel:
        m = CounterModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in COUNTER: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'type': m.counter_type = self.parse_identifier_value()
            elif k == 'name': m.name = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_auto_message_block(self) -> AutoMessageModel:
        m = AutoMessageModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in AUTO_MESSAGE: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'channel': m.channel = self.parse_string_value()
            elif k == 'interval_hours': m.interval_hours = self.parse_int_value()
            elif k == 'message': m.message = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_emoji_block(self) -> EmojiModel:
        m = EmojiModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in EMOJI: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'name': m.name = self.parse_string_value()
            elif k == 'file': m.file = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_sticker_block(self) -> StickerModel:
        m = StickerModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in STICKER: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'name': m.name = self.parse_string_value()
            elif k == 'file': m.file = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_webhook_block(self) -> WebhookModel:
        m = WebhookModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in WEBHOOK: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'channel': m.channel = self.parse_string_value()
            elif k == 'name': m.name = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_scheduled_event_block(self) -> ScheduledEventModel:
        m = ScheduledEventModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in SCHEDULED_EVENT: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'name': m.name = self.parse_string_value()
            elif k == 'description': m.description = self.parse_string_value()
            elif k == 'date': m.date = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_text_template_block(self) -> TextTemplateModel:
        m = TextTemplateModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in TEXT_TEMPLATE: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'name': m.name = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_permission_group_block(self) -> PermissionGroupModel:
        m = PermissionGroupModel()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in PERMISSION_GROUP: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'id': m.group_id = self.parse_identifier_value()
            elif k == 'roles': m.roles = self.parse_role_name_list()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    def parse_bot_block(self) -> BotConfig:
        m = BotConfig()
        self.consume(type=TokenType.LBRACE); self.skip_newlines()
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.RBRACE: break
            token = self.peek()
            if token.type != TokenType.IDENTIFIER: raise ParseError(token.line, token.column, f"Unexpected in BOT: '{token.value}'")
            k = token.value; self.pos += 1; self.consume(type=TokenType.EQUALS)
            if k == 'prefix': m.prefix = self.parse_string_value()
            elif k == 'language': m.language = self.parse_string_value()
            else: self.parse_string_value()
            self.skip_newlines()
        self.consume(type=TokenType.RBRACE)
        return m

    # ── Value helpers ──
    def parse_string_value(self) -> str:
        token = self.peek()
        if token.type == TokenType.STRING:
            self.pos += 1; return token.value
        elif token.type == TokenType.IDENTIFIER and token.value in self.variables:
            self.pos += 1; return self.variables[token.value]
        raise ParseError(token.line, token.column, f"Expected string, got '{token.value}'")

    def parse_int_value(self) -> int:
        token = self.peek()
        if token.type == TokenType.NUMBER:
            self.pos += 1; return int(token.value)
        raise ParseError(token.line, token.column, f"Expected number, got '{token.value}'")

    def parse_bool_value(self) -> bool:
        token = self.peek()
        if token.type == TokenType.IDENTIFIER:
            self.pos += 1
            if token.value == 'true': return True
            elif token.value == 'false': return False
            elif token.value in self.variables:
                return self.variables[token.value].lower() in ('true', '1', 'yes')
        raise ParseError(token.line, token.column, f"Expected bool (true/false), got '{token.value}'")

    def parse_color_value(self) -> str:
        token = self.peek()
        if token.type == TokenType.COLOR:
            self.pos += 1; return token.value
        elif token.type == TokenType.STRING:
            self.pos += 1; return token.value
        elif token.type == TokenType.IDENTIFIER and token.value in self.variables:
            self.pos += 1; return self.variables[token.value]
        raise ParseError(token.line, token.column, f"Expected color (#RRGGBB), got '{token.value}'")

    def parse_identifier_value(self) -> str:
        token = self.peek()
        if token.type == TokenType.IDENTIFIER:
            self.pos += 1
            return self.variables.get(token.value, token.value)
        raise ParseError(token.line, token.column, f"Expected identifier, got '{token.value}'")

    def parse_identifier_list(self) -> list[str]:
        values = [self.parse_identifier_value()]
        while self.peek().type == TokenType.COMMA:
            self.pos += 1; values.append(self.parse_identifier_value())
        return values

    def parse_role_name(self) -> str:
        token = self.peek()
        if token.type == TokenType.STRING:
            self.pos += 1; return token.value
        elif token.type == TokenType.IDENTIFIER:
            self.pos += 1
            return self.variables.get(token.value, token.value)
        raise ParseError(token.line, token.column, f"Expected role name, got '{token.value}'")

    def parse_role_name_list(self) -> list[str]:
        values = [self.parse_role_name()]
        while self.peek().type == TokenType.COMMA:
            self.pos += 1; values.append(self.parse_role_name())
        return values
