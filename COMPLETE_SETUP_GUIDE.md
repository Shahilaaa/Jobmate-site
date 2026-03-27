# JobMate – Complete Setup Guide

## Prerequisites
- Python 3.10+
- PostgreSQL 14+
- pip

---

## Step 1: PostgreSQL Setup

### Option A: Using the setup script
```bash
psql -U postgres -f setup_postgresql.sql
```

### Option B: Manual setup (run in psql as postgres user)
```sql
CREATE DATABASE jobmate;
CREATE USER jobmate_user WITH PASSWORD 'jobmate_pass';
ALTER ROLE jobmate_user SET client_encoding TO 'utf8';
ALTER ROLE jobmate_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE jobmate_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE jobmate TO jobmate_user;
\c jobmate
GRANT ALL ON SCHEMA public TO jobmate_user;
```

---

## Step 2: Configure Environment

Copy `.env.example` to `.env` and edit:
```bash
cp .env.example .env
```

Your `.env` file should look like:
```env
DB_NAME=jobmate
DB_USER=jobmate_user
DB_PASSWORD=jobmate_pass
DB_HOST=127.0.0.1
DB_PORT=5432
DJANGO_DEBUG=1
```

---

## Step 3: Install Dependencies & Run

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Load demo data (50 employees, 10 clients, departments, skills)
python manage.py seed_jobmate

# Run server
python manage.py runserver
```

Open: http://127.0.0.1:8000/

---

## All Pages & URLs

### Public Pages
| Page | URL |
|------|-----|
| Home | `/` |
| About | `/about/` |
| Roles & Skills | `/roles/` |
| Employee Profile List | `/rolesinner/` |
| Employee Profile Detail | `/rolesinner/<id>/` |

### Authentication
| Page | URL |
|------|-----|
| Register (Client/Employee) | `/register/` |
| Login | `/login/` |
| Logout | `/logout/` |
| Admin Login | `/admin_app/admin-login/` |
| Employee Login | `/employee_app/employeelogin/` |

### Client / User Panel (login as client)
| Page | URL |
|------|-----|
| My Profile | `/user_app/myprofile/` |
| Browse Employees | `/user_app/employee/` |
| Employee Profile | `/empprofile/?employee=<id>` |
| Create Task | `/user_app/task/` |
| My Tasks | `/user_app/works/` |
| Task Detail | `/user_app/worksinner/<id>/` |
| Payments | `/user_app/payments/` |
| Support | `/user_app/support/` |
| Chat with Employee | `/chat/<employee_id>/` |
| Notifications | `/notifications/` |

### Employee Dashboard (login as employee)
| Page | URL |
|------|-----|
| Dashboard | `/employee_app/employee-dashboard/` |
| My Tasks | `/employee_app/employee-task/` |
| Task Requests | `/employee_app/task-request/` |
| Task Detail | `/employee_app/task-detail/<id>/` |
| Submit Work | `/employee_app/task-submit/<id>/` |
| My Clients | `/employee_app/clients/` |
| Revenue | `/employee_app/revenue/` |
| My Profile | `/employee_app/employee-profile/` |
| Chat Inbox | `/employee_app/chat/` |

### Admin Dashboard (login as admin/superuser)
| Page | URL |
|------|-----|
| Dashboard | `/dashboard/admin-dashboard/` |
| Employees | `/dashboard/admin-employee/` |
| Clients | `/dashboard/admin-clients/` |
| Revenue | `/dashboard/admin-revenue/` |

---

## Demo Accounts (after running seed_jobmate)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@jobmate.local | admin123 |
| Employees | Various @jobmate.local | employee123 |
| Clients | client1@jobmate.local ... client10@jobmate.local | client123 |

---

## Features

- ✅ Client/User registration & login
- ✅ Employee registration & login  
- ✅ Admin dashboard
- ✅ Browse & search employees (by name/skill/department)
- ✅ Create task requests to employees
- ✅ Employee accepts/rejects tasks
- ✅ Work update submissions with file attachments
- ✅ Real-time task status tracking
- ✅ Payment records auto-created on task completion
- ✅ Chat system (client ↔ employee)
- ✅ Employee chat inbox (view all conversations)
- ✅ Support ticket system
- ✅ Notifications system
- ✅ Profile editing (client and employee)
- ✅ PostgreSQL database
- ✅ File uploads (profile images, work attachments)

