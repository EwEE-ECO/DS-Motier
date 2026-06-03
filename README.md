# DS Motier — Discord Server Builder Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.7%2B-5865f2)](https://discordpy.readthedocs.io)

**DS Motier** — Discord-бот, который строит сервера по текстовому шаблону (DSL v3.0).  
Создавай роли, каналы, категории, форумы, тикеты и многое другое одной командой.

---

## Возможности

- `/build` — загрузи `.txt` файл с описанием сервера → бот создаст всё автоматически
- `/export` — выгрузи текущий сервер в DSL-формат
- `/sync` — синхронизация слеш-команд
- **DSL v3.0**: `SERVER`, `ROLE`, `CATEGORY`, `TEXT`, `VOICE`, `STAGE`, `FORUM`, `WELCOME`, `AUTO_ROLE`, `TICKETS`, `TEMP_VOICE`, `REACTION_ROLE`, `BUTTON_ROLE`, `COUNTER`, `AUTO_MESSAGE`, и другие
- Права доступа через `allow` / `deny` (по именам ролей)
- Режим `readonly` для каналов
- `INCLUDE` — подключение файлов, `VAR` — переменные

---

## Быстрый старт

```bash
# 1. Установи зависимости
pip install -r requirements.txt

# 2. Скопируй config.example.py → config.py и вставь токен бота
cp config.example.py config.py
# Открой config.py и замени TOKEN на свой

# 3. Запусти бота
python main.py
```

### Получение токена

1. Открой [Discord Developer Portal](https://discord.com/developers/applications)
2. Создай приложение → Bot → Copy Token
3. Включи **Privileged Gateway Intents**: `Server Members Intent`, `Message Content Intent`

### Приглашение бота

1. В Developer Portal: **OAuth2 → URL Generator**
2. Scopes: `bot` `applications.commands`
3. Permissions: `Manage Server` `Manage Roles` `Manage Channels` `View Channels` `Send Messages` `Read Message History`
4. Открой ссылку → выбери сервер

---

## Структура проекта

```
DS Motier/
├── main.py              # Точка входа, слеш-команды, ивенты
├── parser.py            # Парсер DSL-шаблонов (токенизатор + парсер)
├── builder.py           # Строитель сервера — создаёт/обновляет роли, каналы и т.д.
├── exporter.py          # Экспорт сервера в DSL-формат
├── models.py            # Data-классы для всех DS L-блоков
├── config.py            # Токен бота (НЕ КОММИТИТЬ)
├── config.example.py    # Пример конфига (для GitHub)
├── welcome.py           # Приветственные сообщения + авто-роль
├── tickets.py           # Тикет-система (кнопки)
├── temp_voice.py        # Временные голосовые комнаты
├── reactions.py         # Роли по реакциям и кнопкам
├── requirements.txt     # Зависимости
├── DOCS.md              # Полная документация DSL
├── Документация DSL.txt # Документация в TXT (кодировка UTF-8)
├── LICENSE              # MIT лицензия
├── .gitignore
├── example.txt          # Базовый пример шаблона
├── example_advanced.txt # Продвинутый пример (INCLUDE, VAR)
├── example_roles.txt    # Пример для INCLUDE
├── example_channels.txt # Пример для INCLUDE
└── programmer_server.txt # Пример: сервер разработчиков
```

---

## Пример шаблона

```dsl
SERVER {
    name = "My Server"
}

ROLE {
    name = "Admin"
    color = "#ff0000"
    permissions = administrator
    hoist = true
}

CATEGORY {
    name = "General"

    TEXT {
        name = "chat"
        topic = "Общий чат"
    }

    VOICE {
        name = "Voice"
        limit = 10
    }
}
```

---

## Команды бота

| Команда | Описание |
|---------|----------|
| `/build` | Загрузить `.txt` шаблон и построить сервер |
| `/export` | Экспортировать сервер в DSL-формат |
| `/sync` | Синхронизировать слеш-команды (только владелец сервера) |

---

## English

**DS Motier** is a Discord bot that builds servers from a text template (DSL v3.0).  
Create roles, channels, categories, forums, tickets, and more with a single command.

### Commands

| Command | Description |
|---------|-------------|
| `/build` | Upload a `.txt` template and build the server |
| `/export` | Export the server to DSL format |
| `/sync` | Sync slash commands (server owner only) |

### Quick Start

```bash
pip install -r requirements.txt
# Copy config.example.py to config.py, add your bot token
python main.py
```

---

## Поддержать

Если проект оказался полезным, можно поддержать автора:

[![YooMoney](https://img.shields.io/badge/ЮMoney-Поддержать-8B5CF6?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMjEuNzVDNi4yIDIxLjc1IDEuNSAxNy4wNSAxLjUgMTEuMjVDMS41IDUuNDUgNi4yIDAuNzUgMTIgMC43NUMxNy44IDAuNzUgMjIuNSA1LjQ1IDIyLjUgMTEuMjVDMjIuNSAxNy4wNSAxNy44IDIxLjc1IDEyIDIxLjc1Wk0xMiAzLjc1QzcuNzIgMy43NSA0LjI1IDcuMjIgNC4yNSAxMS41QzQuMjUgMTUuNzggNy43MiAxOS4yNSAxMiAxOS4yNUMxNi4yOCAxOS4yNSAxOS43NSAxNS43OCAxOS43NSAxMS41QzE5Ljc1IDcuMjIgMTYuMjggMy43NSAxMiAzLjc1WiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)](https://yoomoney.ru/to/4100119169295985)

---

## Лицензия

MIT License
