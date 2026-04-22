# autoscrap

Django + Scrapy stack for scraping car listings (e.g. **Otomoto**, **AutoScout24**), normalizing them into models, and browsing them in the **Django admin** (filters, price history, equipment flags).

## Requirements

- **Python 3.12** (see `pyproject.toml`)

## Setup

1. **Install dependencies** (from repo root), e.g. with [uv](https://github.com/astral-sh/uv):

   ```bash
   uv sync
   ```

   Or use another tool that respects `pyproject.toml` / `uv.lock`.

2. **Configure Django** — copy the template and fill in secrets / DB:

   ```bash
   cp src/autoscrap/environment_template.py src/autoscrap/environment.py
   ```

   Edit `environment.py`: at minimum set `SECRET_KEY`. The template defaults to **SQLite** at `src/db.sqlite3`.

3. **Migrate and (optional) create an admin user** — run commands from **`src/`** so `manage.py` and apps resolve correctly:

   ```bash
   cd src
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Run the admin**:

   ```bash
   cd src
   python manage.py runserver
   ```

## Scrapy crawler

Scrapy project config lives next to Django under `src/` (`scrapy.cfg` → `crawler.settings`). The crawler uses Django items and **`SaveItemPipeline`**, which persists offers through the ORM.

Typical run (from **`src/`**):

```bash
cd src
scrapy crawl otomoto_offers
```

Optional spider argument — custom search URL:

```bash
scrapy crawl otomoto_offers -a listing_url="https://www.otomoto.pl/..."
```

Other spiders (see `src/crawler/spiders/`):

| Spider | Name |
|--------|------|
| Otomoto listings | `otomoto_offers` |
| AutoScout24 listings | `autoscout24_offers` |
| AutoScout (legacy dealer flows) | `autoscout_dealers`, `autoscout_dealer_stats`, `autoscout_dealer_cars` |

### HTTP cache

Enabled in `src/crawler/settings.py` (`HTTPCACHE_ENABLED`, `HTTPCACHE_DIR = "httpcache"`). With default layout, cache data is stored under **`src/httpcache/`** when you run `scrapy` from `src/`.

## Project layout

| Path | Role |
|------|------|
| `src/autoscrap/` | Django project (`settings`, `urls`, `environment.py`) |
| `src/offers/` | `CarOffer`, price history, admin filters |
| `src/dealers/` | Dealer-related models |
| `src/crawler/` | Scrapy settings, spiders, parsers, pipelines |
| `src/manage.py` | Django CLI |

## Environment variables

`src/manage.py` sets:

- `DJANGO_SETTINGS_MODULE=autoscrap.settings`
- `SCRAPY_SETTINGS_MODULE=crawler.settings`

The crawler’s `crawler/settings.py` loads Django so pipelines can use the ORM.

## License

See `LICENSE.md`.
