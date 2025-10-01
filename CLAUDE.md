# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SweetfxDB (sfx.thelazy.net) is a Django web application serving as a comprehensive database for SweetFX, ReShade, and similar graphics modification presets for PC games. Users can browse, download, and share customized shader settings, discuss presets in forums, and view screenshots.

## Development Commands

### Docker Environment (Primary)

```bash
# Build and start the application
docker-compose up --build

# Access at http://localhost:8124/

# Create admin user
docker-compose exec sweetfx python manage.py createsuperuser

# Reset all data (destructive)
docker-compose down -v
```

### Django Management (Inside Container)

```bash
# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Start development server (non-Docker)
python manage.py runserver

# Django shell
python manage.py shell
```

### Testing

Tests are located in each app's `tests.py` file:
- `sweetfx_database/gamedb/tests.py`
- `sweetfx_database/forum/tests.py`
- `sweetfx_database/downloads/tests.py`
- `sweetfx_database/api/tests.py`
- `sweetfx_database/users/tests.py`

Run tests with:
```bash
python manage.py test
```

## Architecture

### Django Apps Structure

The project is organized into several Django apps under `sweetfx_database/`:

- **gamedb**: Core functionality for games, presets, screenshots, and shaders
  - Models: `Game`, `Preset`, `PresetScreenshot`, `Shader`, `UserComment`
  - Image processing logic in `imageLogic.py`
  - Handles preset uploads, screenshot thumbnails, and image optimization

- **forum**: Community discussion forums
  - Models: `Forum`, `ForumThread`, `ForumPost`
  - AI-powered spam detection via `openai_spamjudge.py`
  - Post states: Unchecked (0), Visible (1), Spam (2), Unsure (3), Error (4), Verified spam (5), Mistaken for spam (6)
  - Thread states: Hidden (0), Visible (1)

- **users**: User profiles and authentication
  - Extends Django's built-level authentication
  - Custom context processor `set_style` for theme management

- **downloads**: Download tracking functionality

- **api**: REST API endpoints using Django REST Framework
  - Read-only access for unauthenticated users
  - Pagination: 20 items per page (max 200)

- **silly**: Additional/miscellaneous features

### Key Models Relationships

```
Game
 ├─ Preset (many-to-one)
 │   └─ PresetScreenshot (many-to-one)
 └─ UserComment (generic relation)

Forum
 └─ ForumThread (many-to-one)
     └─ ForumPost (many-to-one)

Preset/PresetScreenshot/Game
 └─ UserComment (generic relation via ContentType)
```

### Important Model Behaviors

- **Counters**: `Game.preset_count` and `Preset.screenshot_count` are automatically updated via signals
- **Forum State Management**: Posts/threads update parent forum state automatically via `post_save` signals
- **Image Processing**: `PresetScreenshot` auto-generates thumbnails and optimizes images on save
- **Visibility**: Most models have `visible` field with `ActiveManager` for filtering published content

### Settings

- Main settings: `sweetfx_database/settings.py`
- Local overrides: `sweetfx_database/settings_local.py` (gitignored)
- Database: SQLite by default (`data/data.sqlite3`)
- Media files: Stored in `media/` directory
- Static files: Collected to `static/` directory
- Secret key can be set via `DJANGO_SECRET_KEY` environment variable

### AI Spam Detection

The forum uses OpenAI-compatible LLMs for spam detection (configured in `settings.py`):
- Environment variables: `SFX_OPENAI_BASE_URL`, `SFX_OPENAI_KEY`, `SFX_OPENAI_MODEL`
- `FORUM_RULES` defines classification criteria
- Automatic user permission removal for repeated spammers
- Custom prompts: `DEFAULT_THREAD_PROMPT`, `DEFAULT_POST_PROMPT`

### URL Structure

- `/games/` - Game and preset browsing
- `/forum/` - Community forums
- `/users/` - User profiles
- `/downloads/` - Download management
- `/api/` - REST API endpoints
- `/admin/` - Django admin interface
- `/accounts/` - Authentication (login, register, etc.)

### Image Processing

PresetScreenshots undergo automatic processing:
1. Compression via `imageLogic.CompressImage`
2. Thumbnail generation (medium: 1000x700, small: 300x200)
3. PNG optimization with `optipng`
4. Both main and comparison images are processed

### Permissions

New users automatically receive:
- `post_on_games` permission
- `post_on_forum` permission

Permissions can be revoked for spam behavior.

## Technology Stack

- Django 2.2.6
- Django REST Framework 3.10.3
- Python 3.10 (via Docker)
- SQLite (default), PostgreSQL supported
- nginx + uWSGI (in Docker)
- Pillow for image processing
- OpenAI API for spam detection
- Jinja2 for AI prompt templates
