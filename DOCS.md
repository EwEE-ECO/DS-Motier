# Discord Server DSL v3.0 — Documentation

DSL (Domain-Specific Language) — a text format for fully describing a Discord server.

---

## Syntax

### Basic value types

```dsl
name = "General"        # String (in quotes)
limit = 10              # Number
nsfw = true             # Boolean (true / false)
color = #ff0000         # Color (hex without quotes)
color = "blue"          # Color (named, with or without quotes)
```

### Comments

```dsl
// This is a comment
// Everything from // to end of line is ignored
```

### Variables (VAR)

```dsl
VAR SERVER_NAME = "My Server"
VAR WELCOME_MSG = "Welcome!"

SERVER {
    name = SERVER_NAME
}
```

### Including files (INCLUDE)

```dsl
INCLUDE "roles.txt"
INCLUDE "channels.txt"
```

Path is relative to the folder from which the bot is running.

---

## Blocks

### SERVER — server settings

```dsl
SERVER {
    name = "My Server"
    description = "Server description"
    verification_level = none     // none | low | medium | high | highest
    default_notifications = all   // all | mentions
}
```

Only `name` is required.

---

### ROLE — role

```dsl
ROLE {
    name = "Admin"
    color = "#ff0000"         // hex or named
    permissions = administrator
    permissions = manage_channels,manage_roles,kick_members
    hoist = true              // display separately
    mentionable = false       // allow mentioning
}
```

**Supported permissions:** `administrator`, `manage_channels`, `manage_roles`, `manage_messages`, `manage_threads`, `manage_events`, `kick_members`, `ban_members`, `moderate_members`, `mention_everyone`, `view_audit_log`, `manage_webhooks`, `manage_nicknames`, `create_instant_invite`, `send_messages`, `embed_links`, `attach_files`, `read_message_history`, `use_external_emojis`, `use_external_stickers`, `add_reactions`, `connect`, `speak`, `move_members`, `stream`, `priority_speaker`, `request_to_speak`, and others.

---

### CATEGORY — category

```dsl
CATEGORY {
    name = "Administration"

    // Permissions for the whole category (inherited by channels)
    allow = "Admin","Moderator"
    deny = "Member"

    TEXT { name = "general" }
    VOICE { name = "Voice" }
    FORUM { name = "Forum" }
    STAGE { name = "Stage" }
}
```

Channels inside a category inherit the parent's `allow`/`deny`.  
If a channel has its own `allow`/`deny`, they are applied in addition to the parent's.

---

### TEXT — text channel

```dsl
TEXT {
    name = "general"
    topic = "Main chat"
    slowmode = 5             // delay in seconds
    nsfw = false
    readonly = true          // read-only (prevents sending)
    send_messages = true
    create_threads = true

    // Access permissions (override parent)
    allow = "Role1","Role2"
    deny = "Role3"
}
```

`readonly = true` disables `send_messages`, `add_reactions`, `create_public_threads`, `create_private_threads`, `send_messages_in_threads` for `@everyone`.

---

### VOICE — voice channel

```dsl
VOICE {
    name = "General Voice"
    limit = 10               // 0 = unlimited
    bitrate = 64000          // from 8000 to 384000 (96000 for boosts)
    video_quality = auto     // auto | 720p | 1080p
    allow = "Role1"
    deny = "Role2"
}
```

---

### STAGE — Stage channel

```dsl
STAGE {
    name = "Podcast"
    allow = "Role1"
    deny = "Role2"
}
```

Requires Community mode enabled on the server.

---

### FORUM — forum

```dsl
FORUM {
    name = "help-forum"
    topic = "Help forum"
    slowmode = 5
    nsfw = false
    default_reaction = "👍"
    tags = Python,Java,Rust,JavaScript
    allow = "Role1"
    deny = "Role2"
}
```

Requires Community mode enabled on the server.

---

### RULES_CHANNEL — rules channel

```dsl
RULES_CHANNEL {
    name = "rules"
}
```

Discord will automatically set it as the rules channel.

---

### COMMUNITY — community settings

```dsl
COMMUNITY {
    enabled = true
    rules_channel = "rules"
    updates_channel = "announcements"
}
```

---

### WELCOME — welcome message

```dsl
WELCOME {
    channel = "welcome"
    message = "Welcome to the server, {user}!"
}
```

**Variables for message:**

| Variable | Description |
|------------|----------|
| `{user}` | User mention (@user) |
| `{username}` | Username |
| `{member_count}` | Member count |
| `{server_name}` | Server name |

---

### AUTO_ROLE — automatic role assignment

```dsl
AUTO_ROLE {
    role = "Member"
}
```

Assigned to new members immediately upon joining.

---

### REACTION_ROLE — role via reaction

```dsl
REACTION_ROLE {
    channel = "roles"
    message = "Choose a programming language"
    emoji = "🐍"
    role = "Python"
}
```

On reaction add — role assigned. On reaction remove — removed.

---

### BUTTON_ROLE — role via button

```dsl
BUTTON_ROLE {
    channel = "roles"
    label = "Python"
    role = "Python"
    style = primary          // primary | secondary | success | danger
}
```

Button press — role toggles on/off.

---

### TICKETS — ticket system

```dsl
TICKETS {
    category = "Tickets"
    staff_roles = "Admin","Moderator"
    create_channel_name = "create-ticket"
    transcript = true
    auto_close_days = 30
}
```

- A "Create Ticket" button appears in the `create_channel_name` channel
- Ticket channel is visible only to the creator and staff roles
- The "Close" button deletes the channel after 5 seconds

---

### TEMP_VOICE — temporary voice channels

```dsl
TEMP_VOICE {
    name = "➕ Create Room"
    category = "Voice"
    user_limit = 10
}
```

When a user joins the channel named `name`, their personal room is created.  
When all participants leave, the room is automatically deleted.

---

### LOGS — logging

```dsl
LOGS {
    joins = "member-logs"
    leaves = "member-logs"
    message_delete = "mod-logs"
    message_edit = "mod-logs"
    voice_events = "voice-logs"
    moderation = "mod-logs"
}
```

> **Note:** logging system is under development.

---

### COUNTER — counter

```dsl
COUNTER {
    type = members           // members | bots | online | boosts
    name = "👥 Members: {count}"
}
```

Creates a voice channel where `{count}` is replaced with the current value.

---

### AUTO_MESSAGE — automatic message

```dsl
AUTO_MESSAGE {
    channel = "general"
    interval_hours = 24
    message = "Don't forget to show your project!"
}
```

Sends a message to the channel every `interval_hours` hours.

---

### EMOJI — custom emoji

```dsl
EMOJI {
    name = "python"
    file = "./emojis/python.png"
}
```

---

### STICKER — sticker

```dsl
STICKER {
    name = "approved"
    file = "./stickers/approved.png"
}
```

---

### WEBHOOK — webhook

```dsl
WEBHOOK {
    channel = "announcements"
    name = "News"
}
```

---

### SCHEDULED_EVENT — scheduled event

```dsl
SCHEDULED_EVENT {
    name = "Code Review"
    description = "Community project reviews"
    date = "2026-07-01"
}
```

---

### TEXT_TEMPLATE — template channels

```dsl
TEXT_TEMPLATE {
    name = "project-{number}"
    count = 5
}
```

Creates channels `project-1`, `project-2`, `project-3`, `project-4`, `project-5`.

---

### PERMISSION_GROUP — role group

```dsl
PERMISSION_GROUP {
    id = staff
    roles = "Admin","Moderator"
}
```

Used in `allow`/`deny` by `id`:

```dsl
CATEGORY {
    name = "Staff"
    allow = staff
}
```

---

### BOT — bot settings

```dsl
BOT {
    prefix = "!"
    language = "en"
}
```

---

## Full example

```dsl
SERVER {
    name = "Developer Hub"
}

ROLE { name = "Owner" color = "#ff0000" permissions = administrator hoist = true }
ROLE { name = "Member" color = "#99aab5" }

AUTO_ROLE { role = "Member" }

CATEGORY {
    name = "General"

    TEXT { name = "welcome" topic = "Welcome!" readonly = true }
    TEXT { name = "chat" topic = "General chat" }
    VOICE { name = "Voice" limit = 10 }
}

WELCOME {
    channel = "welcome"
    message = "Welcome, {user}!"
}

TICKETS {
    category = "Tickets"
    staff_roles = "Owner"
}

TEMP_VOICE {
    name = "➕ Create Room"
}
```

---

## Export

The `/export` command exports the current server to DSL format.  
The downloaded file can be edited and uploaded via `/build`.
