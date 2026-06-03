# DS Motier — Discord Server Builder Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.7%2B-5865f2)](https://discordpy.readthedocs.io)

**DS Motier** is an open-source Discord bot that builds servers from a text template (DSL v3.0).  
Create roles, channels, categories, forums, tickets, and more with a single command.

---

## Features

- `/build` — upload .txt template → bot builds the server
- `/export` — export current server to DSL format
- `/sync` — sync slash commands (owner only)
- **DSL v3.0**: `SERVER`, `ROLE`, `CATEGORY`, `TEXT`, `VOICE`, `STAGE`, `FORUM`, `WELCOME`, `AUTO_ROLE`, `TICKETS`, `TEMP_VOICE`, `REACTION_ROLE`, `BUTTON_ROLE`, `COUNTER`, `AUTO_MESSAGE`, and more
- allow/deny permission selectors
- readonly channels
- `INCLUDE` (multi-file), `VAR` (variables)

---

## Quick Start

```bash
pip install -r requirements.txt
cp config.example.py config.py
# Edit config.py → add your bot token
python main.py
```

### Getting a Token

1. Open [Discord Developer Portal](https://discord.com/developers/applications)
2. Create application → Bot → Copy Token
3. Enable **Privileged Gateway Intents**: `Server Members Intent`, `Message Content Intent`

### Inviting the Bot

1. In Developer Portal: **OAuth2 → URL Generator**
2. Scopes: `bot` `applications.commands`
3. Permissions: `Manage Server` `Manage Roles` `Manage Channels` `View Channels` `Send Messages` `Read Message History`
4. Open the URL → select your server

---

## Project Structure

```
DS Motier/
├── main.py              # Entry point, slash commands, events
├── parser.py            # DSL parser (tokenizer + parser)
├── builder.py           # Server builder — creates/updates roles, channels, etc.
├── exporter.py          # Server export to DSL format
├── models.py            # Data classes for all DSL blocks
├── config.py            # Bot token (DO NOT COMMIT)
├── config.example.py    # Example config (for GitHub)
├── welcome.py           # Welcome messages + auto-role
├── tickets.py           # Ticket system (buttons)
├── temp_voice.py        # Temp voice channels
├── reactions.py         # Reaction and button roles
├── requirements.txt     # Dependencies
├── DOCS.md              # Full DSL documentation
├── LICENSE              # MIT license
├── .gitignore
├── example.txt          # Basic template example
├── example_advanced.txt # Advanced example (INCLUDE, VAR)
├── example_roles.txt    # Example for INCLUDE
├── example_channels.txt # Example for INCLUDE
└── programmer_server.txt # Developer server example
```

---

## Links
- Website: https://ewee-eco.github.io/DS-Motier/
- Discord: https://discord.gg/34YmpcVjrR
- Docs: https://github.com/EwEE-ECO/DS-Motier/blob/main/DOCS.md

---

## Support

If you find this project useful, consider supporting the author:

[![YooMoney](https://img.shields.io/badge/YooMoney-Donate-8B5CF6?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMjEuNzVDNi4yIDIxLjc1IDEuNSAxNy4wNSAxLjUgMTEuMjVDMS41IDUuNDUgNi4yIDAuNzUgMTIgMC43NUMxNy44IDAuNzUgMjIuNSA1LjQ1IDIyLjUgMTEuMjVDMjIuNSAxNy4wNSAxNy44IDIxLjc1IDEyIDIxLjc1Wk0xMiAzLjc1QzcuNzIgMy43NSA0LjI1IDcuMjIgNC4yNSAxMS41QzQuMjUgMTUuNzggNy43MiAxOS4yNSAxMiAxOS4yNUMxNi4yOCAxOS4yNSAxOS43NSAxNS43OCAxOS43NSAxMS41QzE5Ljc1IDcuMjIgMTYuMjggMy43NSAxMiAzLjc1WiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)](https://yoomoney.ru/to/4100119169295985)

---

## License

MIT License
