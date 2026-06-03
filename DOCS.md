# Discord Server DSL v3.0 — Документация

DSL (Domain-Specific Language) — текстовый формат для полного описания Discord-сервера.

---

## Синтаксис

### Базовые типы значений

```dsl
name = "General"        # Строка (в кавычках)
limit = 10              # Число
nsfw = true             # Логическое (true / false)
color = #ff0000         # Цвет (hex без кавычек)
color = "blue"          # Цвет (именованный, в кавычках или без)
```

### Комментарии

```dsl
// Это комментарий
// Всё от // до конца строки игнорируется
```

### Переменные (VAR)

```dsl
VAR SERVER_NAME = "My Server"
VAR WELCOME_MSG = "Добро пожаловать!"

SERVER {
    name = SERVER_NAME
}
```

### Подключение файлов (INCLUDE)

```dsl
INCLUDE "roles.txt"
INCLUDE "channels.txt"
```

Путь указывается относительно папки, из которой запущен бот.

---

## Блоки

### SERVER — настройки сервера

```dsl
SERVER {
    name = "My Server"
    description = "Описание сервера"
    verification_level = none     // none | low | medium | high | highest
    default_notifications = all   // all | mentions
}
```

Обязателен только `name`.

---

### ROLE — роль

```dsl
ROLE {
    name = "Admin"
    color = "#ff0000"         // hex или именованный
    permissions = administrator
    permissions = manage_channels,manage_roles,kick_members
    hoist = true              // отображать отдельно
    mentionable = false       // разрешить упоминание
}
```

**Поддерживаемые разрешения:** `administrator`, `manage_channels`, `manage_roles`, `manage_messages`, `manage_threads`, `manage_events`, `kick_members`, `ban_members`, `moderate_members`, `mention_everyone`, `view_audit_log`, `manage_webhooks`, `manage_nicknames`, `create_instant_invite`, `send_messages`, `embed_links`, `attach_files`, `read_message_history`, `use_external_emojis`, `use_external_stickers`, `add_reactions`, `connect`, `speak`, `move_members`, `stream`, `priority_speaker`, `request_to_speak`, и другие.

---

### CATEGORY — категория

```dsl
CATEGORY {
    name = "Administration"

    // Права для всей категории (наследуются каналами)
    allow = "Admin","Moderator"
    deny = "Member"

    TEXT { name = "general" }
    VOICE { name = "Voice" }
    FORUM { name = "Forum" }
    STAGE { name = "Stage" }
}
```

Каналы внутри категории наследуют `allow`/`deny` родителя.  
Если у канала свои `allow`/`deny` — они применяются вдобавок к родительским.

---

### TEXT — текстовый канал

```dsl
TEXT {
    name = "general"
    topic = "Основной чат"
    slowmode = 5             // задержка в секундах
    nsfw = false
    readonly = true          // только чтение (запрет отправки)
    send_messages = true
    create_threads = true

    // Права доступа (переопределяют родительские)
    allow = "Role1","Role2"
    deny = "Role3"
}
```

`readonly = true` запрещает `send_messages`, `add_reactions`, `create_public_threads`, `create_private_threads`, `send_messages_in_threads` для `@everyone`.

---

### VOICE — голосовой канал

```dsl
VOICE {
    name = "General Voice"
    limit = 10               // 0 = безлимит
    bitrate = 64000          // от 8000 до 384000 (96000 для boosts)
    video_quality = auto     // auto | 720p | 1080p
    allow = "Role1"
    deny = "Role2"
}
```

---

### STAGE — Stage канал

```dsl
STAGE {
    name = "Podcast"
    allow = "Role1"
    deny = "Role2"
}
```

Требует включённого Community-режима на сервере.

---

### FORUM — форум

```dsl
FORUM {
    name = "help-forum"
    topic = "Форум помощи"
    slowmode = 5
    nsfw = false
    default_reaction = "👍"
    tags = Python,Java,Rust,JavaScript
    allow = "Role1"
    deny = "Role2"
}
```

Требует включённого Community-режима на сервере.

---

### RULES_CHANNEL — канал правил

```dsl
RULES_CHANNEL {
    name = "rules"
}
```

Discord автоматически назначит его как канал правил.

---

### COMMUNITY — настройки сообщества

```dsl
COMMUNITY {
    enabled = true
    rules_channel = "rules"
    updates_channel = "announcements"
}
```

---

### WELCOME — приветственное сообщение

```dsl
WELCOME {
    channel = "welcome"
    message = "Добро пожаловать на сервер, {user}!"
}
```

**Переменные для message:**

| Переменная | Описание |
|------------|----------|
| `{user}` | Упоминание пользователя (@user) |
| `{username}` | Имя пользователя |
| `{member_count}` | Количество участников |
| `{server_name}` | Название сервера |

---

### AUTO_ROLE — автоматическая выдача роли

```dsl
AUTO_ROLE {
    role = "Member"
}
```

Выдаётся новому участнику сразу после входа.

---

### REACTION_ROLE — роль по реакции

```dsl
REACTION_ROLE {
    channel = "roles"
    message = "Выберите язык программирования"
    emoji = "🐍"
    role = "Python"
}
```

При добавлении реакции — роль выдаётся. При снятии — забирается.

---

### BUTTON_ROLE — роль по кнопке

```dsl
BUTTON_ROLE {
    channel = "roles"
    label = "Python"
    role = "Python"
    style = primary          // primary | secondary | success | danger
}
```

Нажатие на кнопку — роль добавляется/убирается (toggle).

---

### TICKETS — тикет-система

```dsl
TICKETS {
    category = "Tickets"
    staff_roles = "Admin","Moderator"
    create_channel_name = "create-ticket"
    transcript = true
    auto_close_days = 30
}
```

- В канале `create_channel_name` появляется кнопка "Create Ticket"
- Тикет-канал виден только создателю и staff-ролям
- Кнопка "Close" удаляет канал через 5 секунд

---

### TEMP_VOICE — временные голосовые комнаты

```dsl
TEMP_VOICE {
    name = "➕ Create Room"
    category = "Voice"
    user_limit = 10
}
```

Когда пользователь заходит в канал с именем `name`, создаётся его личная комната.  
При выходе всех участников — комната автоматически удаляется.

---

### LOGS — логирование

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

> **Примечание:** система логов находится в разработке.

---

### COUNTER — счётчик

```dsl
COUNTER {
    type = members           // members | bots | online | boosts
    name = "👥 Members: {count}"
}
```

Создаёт голосовой канал, в котором `{count}` заменяется на текущее значение.

---

### AUTO_MESSAGE — автоматическое сообщение

```dsl
AUTO_MESSAGE {
    channel = "general"
    interval_hours = 24
    message = "Не забудьте показать свой проект!"
}
```

Отправляет сообщение в канал каждые `interval_hours` часов.

---

### EMOJI — пользовательский эмодзи

```dsl
EMOJI {
    name = "python"
    file = "./emojis/python.png"
}
```

---

### STICKER — стикер

```dsl
STICKER {
    name = "approved"
    file = "./stickers/approved.png"
}
```

---

### WEBHOOK — вебхук

```dsl
WEBHOOK {
    channel = "announcements"
    name = "News"
}
```

---

### SCHEDULED_EVENT — запланированное событие

```dsl
SCHEDULED_EVENT {
    name = "Code Review"
    description = "Разбор проектов сообщества"
    date = "2026-07-01"
}
```

---

### TEXT_TEMPLATE — каналы по шаблону

```dsl
TEXT_TEMPLATE {
    name = "project-{number}"
    count = 5
}
```

Создаст каналы `project-1`, `project-2`, `project-3`, `project-4`, `project-5`.

---

### PERMISSION_GROUP — группа ролей

```dsl
PERMISSION_GROUP {
    id = staff
    roles = "Admin","Moderator"
}
```

Используется в `allow`/`deny` по `id`:

```dsl
CATEGORY {
    name = "Staff"
    allow = staff
}
```

---

### BOT — настройки бота

```dsl
BOT {
    prefix = "!"
    language = "ru"
}
```

---

## Полный пример

```dsl
SERVER {
    name = "Developer Hub"
}

ROLE { name = "Owner" color = "#ff0000" permissions = administrator hoist = true }
ROLE { name = "Member" color = "#99aab5" }

AUTO_ROLE { role = "Member" }

CATEGORY {
    name = "General"

    TEXT { name = "welcome" topic = "Добро пожаловать!" readonly = true }
    TEXT { name = "chat" topic = "Общий чат" }
    VOICE { name = "Voice" limit = 10 }
}

WELCOME {
    channel = "welcome"
    message = "Добро пожаловать, {user}!"
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

## Экспорт

Команда `/export` выгружает текущий сервер в DSL-формат.  
Скачанный файл можно отредактировать и загрузить через `/build`.
