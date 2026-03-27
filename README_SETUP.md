# JobMate (Django + PostgreSQL) – Setup

## 1) Create PostgreSQL DB

```sql
-- psql terminal
CREATE DATABASE jobmate;
CREATE USER jobmate_user WITH PASSWORD 'jobmate_pass';
ALTER ROLE jobmate_user SET client_encoding TO 'utf8';
ALTER ROLE jobmate_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE jobmate_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE jobmate TO jobmate_user;
```

## 2) Configure environment

Create a `.env` file (you can copy `.env.example`).

```env
DB_NAME=jobmate
DB_USER=jobmate_user
DB_PASSWORD=jobmate_pass
DB_HOST=127.0.0.1
DB_PORT=5432
DJANGO_DEBUG=1
```

## 3) Install & run

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser

# optional demo data
python manage.py seed_jobmate

python manage.py runserver
```

## 4) Pages / Routes

- Public
  - `/` Home
  - `/about/`
  - `/roles/`

- Auth
  - `/register/` (creates Client or Employee)
  - `/login/`
  - `/logout/`

- Client/User panel
  - `/user_app/employee/` list employees
  - `/user_app/task/` create task request
  - `/user_app/works/` my tasks
  - `/user_app/worksinner/<id>/` task detail

- Employee panel
  - `/employee_app/employee-dashboard/`
  - `/employee_app/employee-task/`
  - `/employee_app/task-detail/<id>/`
  - `/employee_app/task-submit/<id>/`

- Admin panel
  - `/dashboard/admin-dashboard/`
  - `/dashboard/admin-employee/`
  - `/dashboard/admin-clients/`
  - `/dashboard/admin-revenue/`

## Demo accounts (if you ran `seed_jobmate`)

- Admin: `admin@jobmate.local` / `admin123`
- Employees: `<random>@jobmate.local` / `employee123`
- Clients: `client1@jobmate.local` / `client123`
