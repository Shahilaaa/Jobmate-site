# JobMate - Full Setup Guide

## Requirements
- Python 3.10+
- PostgreSQL 13+ (or use SQLite for development)
- pip

## Quick Start

### 1. Install Python Dependencies

```bash
pip install django psycopg2-binary pillow python-dotenv
```

### 2. Configure Database

**Option A: PostgreSQL (Recommended for production)**

Create `.env` file in the project root:
```
DB_NAME=jobmate_db
DB_USER=jobmate_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
DJANGO_DEBUG=1
```

Then create the PostgreSQL database:
```bash
psql -U postgres -c "CREATE USER jobmate_user WITH PASSWORD 'your_password';"
psql -U postgres -c "CREATE DATABASE jobmate_db OWNER jobmate_user;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE jobmate_db TO jobmate_user;"
```

**Option B: SQLite (Development only)**

Just skip the `.env` file. The app will automatically use SQLite.

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Seed Initial Data (Departments & Skills)

```bash
python manage.py seed_data
```

For demo users (admin, employee, client with sample tasks):
```bash
python manage.py seed_data --demo
```

Demo credentials (if `--demo` used):
| Role     | Email                  | Password    |
|----------|------------------------|-------------|
| Admin    | admin@jobmate.com      | Admin@1234  |
| Employee | john@jobmate.com       | Emp@1234    |
| Client   | client@jobmate.com     | Client@1234 |

### 5. Create Your Own Admin

```bash
python manage.py createsuperuser
```

### 6. Start the Server

```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000

---

## Page URLs

### Public Pages
| Page            | URL                              |
|----------------|----------------------------------|
| Home            | /                                |
| About           | /about/                          |
| Roles & Skills  | /roles/                          |
| Register        | /register/                       |
| Login (Client)  | /login/                          |

### Client (User) Pages (requires login as Client)
| Page            | URL                              |
|----------------|----------------------------------|
| My Profile      | /user_app/myprofile/             |
| Browse Employees| /user_app/employee/              |
| My Works        | /user_app/works/                 |
| Request Task    | /user_app/task/                  |
| Payments        | /user_app/payments/              |
| Support         | /user_app/support/               |
| Chat            | /chat/<employee_id>/             |

### Employee Dashboard (requires login as Employee)
| Page            | URL                              |
|----------------|----------------------------------|
| Dashboard       | /employee_app/employee-dashboard/|
| Task List       | /employee_app/employee-task/     |
| Pending Requests| /employee_app/task-request/      |
| Task Detail     | /employee_app/task-detail/<id>/  |
| Submit Work     | /employee_app/task-submit/<id>/  |
| My Clients      | /employee_app/clients/           |
| Revenue         | /employee_app/revenue/           |
| Profile         | /employee_app/employee-profile/  |
| Chat Inbox      | /employee_app/chat/              |
| Login           | /employee_app/employeelogin/     |

### Admin Dashboard (requires login as Admin/Superuser)
| Page            | URL                              |
|----------------|----------------------------------|
| Dashboard       | /admin_app/admin-dashboard/      |
| Employees       | /admin_app/admin-employee/       |
| Clients         | /admin_app/admin-clients/        |
| Revenue         | /admin_app/admin-revenue/        |
| Login           | /admin_app/admin-login/          |

---

## User Roles & Flow

### Client Flow
1. Register at `/register/` (choose User or Employer)
2. Login at `/login/`
3. Browse employees at `/user_app/employee/`
4. Click an employee → View profile → Request Task or Chat
5. Track work at `/user_app/works/`
6. View payments at `/user_app/payments/`

### Employee Flow
1. Register at `/register/` (choose Employee, select department & skill)
2. Login at `/employee_app/employeelogin/`
3. Check pending requests at task-request page
4. Accept/Reject requests
5. Submit work updates at task-submit page
6. View chat from clients at `/employee_app/chat/`
7. Edit profile at employee-profile page

### Admin Flow
1. Create superuser with `python manage.py createsuperuser`
2. Login at `/admin_app/admin-login/`
3. Monitor employees, clients, revenue

---

## Media Files Setup

For production, configure MEDIA_ROOT in settings. For development it's automatic:
- Profile images: `media/profiles/`
- Work attachments: `media/work/`

---

## Troubleshooting

**DoesNotExist errors**: Run `python manage.py migrate` and `python manage.py seed_data`

**Images not showing**: Ensure `MEDIA_URL` and `MEDIA_ROOT` are set in settings.py (already done)

**PostgreSQL connection refused**: Start PostgreSQL service with `sudo service postgresql start`

**Static files missing**: Run `python manage.py collectstatic` for production
