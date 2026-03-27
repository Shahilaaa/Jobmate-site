#!/bin/bash
# ============================================================
# JobMate - PostgreSQL Full Setup Script
# Run this script after extracting the project zip
# ============================================================

set -e
echo ""
echo "======================================================"
echo "  JobMate - PostgreSQL Setup"
echo "======================================================"

# ---- Step 1: Install dependencies ----
echo ""
echo "[1/6] Installing Python dependencies..."
pip install django psycopg2-binary pillow python-dotenv

# ---- Step 2: Create .env ----
if [ ! -f ".env" ]; then
    echo ""
    echo "[2/6] Creating .env file..."
    echo "Please provide your PostgreSQL credentials:"
    read -p "  Database name [jobmate_db]: " DB_NAME
    DB_NAME=${DB_NAME:-jobmate_db}
    read -p "  Database user [jobmate_user]: " DB_USER
    DB_USER=${DB_USER:-jobmate_user}
    read -s -p "  Database password: " DB_PASSWORD
    echo ""
    read -p "  Database host [127.0.0.1]: " DB_HOST
    DB_HOST=${DB_HOST:-127.0.0.1}
    read -p "  Database port [5432]: " DB_PORT
    DB_PORT=${DB_PORT:-5432}

    cat > .env << ENV_EOF
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DJANGO_DEBUG=1
ENV_EOF
    echo "  .env file created."
else
    echo "[2/6] .env file already exists, skipping."
    source .env 2>/dev/null || true
fi

# ---- Step 3: Create PostgreSQL database ----
echo ""
echo "[3/6] Creating PostgreSQL database and user..."
source .env 2>/dev/null || true

# Try to create database (may fail if already exists)
psql -U postgres -c "CREATE USER ${DB_USER:-jobmate_user} WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || echo "  (User may already exist)"
psql -U postgres -c "CREATE DATABASE ${DB_NAME:-jobmate_db} OWNER ${DB_USER:-jobmate_user};" 2>/dev/null || echo "  (Database may already exist)"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME:-jobmate_db} TO ${DB_USER:-jobmate_user};" 2>/dev/null || true

# ---- Step 4: Run migrations ----
echo ""
echo "[4/6] Running database migrations..."
python manage.py migrate

# ---- Step 5: Load seed data ----
echo ""
echo "[5/6] Loading seed data (departments, skills)..."
python manage.py shell << 'PYTHONEOF'
from pages.models import Department, Skill

# Create departments
departments_data = {
    "Software Development": ["Python", "JavaScript", "React", "Django", "Node.js", "Java", "Flutter", "iOS Development", "Android Development"],
    "Design": ["UI Design", "Graphic Design", "Logo Design", "Motion Graphics", "Figma", "Adobe XD"],
    "Digital Marketing": ["SEO", "Social Media Marketing", "Google Ads", "Content Marketing", "Email Marketing"],
    "Data & Analytics": ["Data Analysis", "Machine Learning", "Power BI", "Tableau", "Excel Analytics"],
    "IT Support": ["Networking", "System Administration", "Cybersecurity", "Cloud Computing", "DevOps"],
    "Content Writing": ["Blog Writing", "Copywriting", "Technical Writing", "Script Writing", "Proofreading"],
    "Admin & Operations": ["Project Management", "Virtual Assistant", "HR Operations", "Accounting", "Customer Support"],
}

created = 0
for dept_name, skills in departments_data.items():
    dept, _ = Department.objects.get_or_create(name=dept_name)
    for skill_name in skills:
        _, created_now = Skill.objects.get_or_create(department=dept, name=skill_name)
        if created_now:
            created += 1

print(f"  Created {Department.objects.count()} departments and {Skill.objects.count()} skills ({created} new)")
PYTHONEOF

# ---- Step 6: Create superuser ----
echo ""
echo "[6/6] Create admin superuser..."
echo "  (This will be your admin login for /admin/ and /admin_app/admin-login/)"
python manage.py createsuperuser

echo ""
echo "======================================================"
echo "  Setup Complete!"
echo "======================================================"
echo ""
echo "  Start the server with:"
echo "    python manage.py runserver"
echo ""
echo "  Then open: http://127.0.0.1:8000"
echo ""
echo "  Admin login: http://127.0.0.1:8000/admin_app/admin-login/"
echo "  Employee login: http://127.0.0.1:8000/employee_app/employeelogin/"
echo "  User login: http://127.0.0.1:8000/login/"
echo ""
