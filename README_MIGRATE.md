# JobMate — Setup Guide (All Platforms)

## Step 1 — Install PostgreSQL

| Platform | Instructions |
|----------|-------------|
| **macOS** | Download **Postgres.app** → https://postgresapp.com → drag to Applications → open → click Initialize |
| **Windows** | Download from https://postgresql.org/download/windows → install with defaults |
| **Linux** | `sudo apt install postgresql postgresql-contrib` |

## Step 2 — Create the database

```bash
# macOS / Linux
psql -U postgres -c "CREATE DATABASE jobmate_db;"

# Windows (run in pgAdmin SQL Tool or psql)
CREATE DATABASE jobmate_db;
```

## Step 3 — Configure .env

Copy `.env.example` to `.env` and fill in your credentials:
```
DB_NAME=jobmate_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

## Step 4 — Install Python packages

```bash
pip install -r requirements.txt
```

## Step 5 — Run migrations

```bash
python manage.py migrate
```

✅ Works on **both fresh and existing databases** — no extra flags needed.
The migration automatically detects whether tables exist and skips creation if they do.

## Step 6 — Start the server

```bash
python manage.py runserver
```

---

## Default logins

| Role     | Email                    | Password      |
|----------|--------------------------|---------------|
| Admin    | admin@jobmate.com        | Admin@1234    |
| Employee | alice.emp@jobmate.com    | Employee@1234 |
| Employee | bob.emp@jobmate.com      | Employee@1234 |
| Client   | carol.client@jobmate.com | Client@1234   |
| Client   | david.client@jobmate.com | Client@1234   |
| Client   | eva.client@jobmate.com   | Client@1234   |

---

## 📧 Email / Enquiry Form

**Email works out of the box** — no setup needed on the other machine.

The About page enquiry form sends email via the built-in JobMate Gmail account.
This is configured as a hardcoded fallback in `settings.py`, so it works even
if `EMAIL_HOST_PASSWORD` is blank or missing from your `.env`.

To use **your own Gmail account** instead, set in `.env`:
```
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop   ← 16-char App Password, no spaces
ENQUIRY_RECIPIENT=your@gmail.com
```
Then restart the server. Test with: `python manage.py test_email`
