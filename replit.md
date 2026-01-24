# Lucia Filter Bot

## Overview

Lucia Filter Bot is a Telegram bot designed for automated media filtering and group management. It allows users to index, store, and search media files (documents, videos, audio) from Telegram channels using MongoDB as the backend database. The bot supports premium subscriptions, referral systems, file streaming via web interface, and multiple verification methods for users.

Key capabilities:
- Auto-indexing media files from configured Telegram channels
- Fast file searching with pagination and fuzzy matching
- Dual MongoDB database support with automatic failover
- Premium subscription management with expiry reminders
- Web-based file streaming with VLC/MX Player integration
- Force subscription and user verification systems
- Broadcast messaging to users and groups

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Pyrogram (pyrofork)**: Used as the Telegram MTProto client library for bot interactions
- **Plugin-based architecture**: Bot functionality is modular, with plugins located in the `plugins/` directory
- **Multi-client support**: Can run multiple bot tokens simultaneously for load distribution (configured via `MULTI_TOKEN` environment variables)

### Database Layer
- **MongoDB with Motor**: Async MongoDB driver for non-blocking database operations
- **Dual database setup**: Primary and secondary MongoDB instances with automatic switching when primary reaches capacity (80MB threshold)
- **umongo ODM**: Document-object mapping for structured data models (Media, Media2 schemas)
- **Collections**: Users, groups, premium subscriptions, verification codes, referrals, connection settings

### Web Server
- **aiohttp**: Provides HTTP server for file streaming and health checks
- **Jinja2 templating**: HTML templates for video streaming pages (`Lucia/template/`)
- **Custom byte streaming**: Efficient file streaming from Telegram servers to web clients

### File Processing
- **Media indexing**: Automatically saves file metadata (name, size, type, caption) when media is posted to configured channels
- **Search functionality**: Full-text search on file names with fuzzy matching (fuzzywuzzy library)
- **IMDb integration**: Fetches movie information using cinemagoer library

### Configuration
- **Environment variables**: All configuration via environment variables (see `info.py`)
- **No config files**: Settings are parsed at runtime from environment

### Key Design Decisions

1. **Dual Database for Scalability**: When primary MongoDB nears capacity, new files automatically save to secondary database. Both databases are queried for searches.

2. **Async-First Architecture**: All I/O operations (database, Telegram API, HTTP) use async/await for high concurrency.

3. **Plugin System**: Each feature (broadcast, premium, indexing) is a separate plugin file, making the codebase modular and maintainable.

4. **Keep-Alive Ping**: Background task pings the bot's URL every 2 minutes to prevent hosting platforms from sleeping the instance.

## External Dependencies

### Telegram API
- Bot Token from @BotFather
- API_ID and API_HASH from my.telegram.org
- Requires channels/groups for: logging, file storage (BIN_CHANNEL), movie updates, premium logs

### MongoDB
- Primary: `DATABASE_URI` - Main database for files and user data
- Secondary: `DATABASE_URI2` - Backup database when primary is full
- Uses MongoDB Atlas or self-hosted instances with SRV connection strings

### Third-Party Services
- **URL Shorteners**: Shortzy library for link shortening (optional)
- **Telegraph**: Image hosting for bot thumbnails
- **IMDb (cinemagoer)**: Movie metadata lookup

### Python Dependencies
Key libraries from requirements.txt:
- `pyrofork`: Telegram client
- `motor`: Async MongoDB driver
- `aiohttp`: Web server and HTTP client
- `fuzzywuzzy`: Fuzzy string matching for search
- `jinja2`: Template rendering
- `Pillow/opencv-python-headless`: Image processing
- `pytz`: Timezone handling (Asia/Kolkata default)