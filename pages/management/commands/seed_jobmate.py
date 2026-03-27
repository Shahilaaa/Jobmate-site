import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from pages.models import Department, Skill, Profile, UserRole, EmployeeProfile, ClientProfile


FIRST_NAMES = [
    "Aarav", "Diya", "Arjun", "Ananya", "Ishan", "Meera", "Rahul", "Nisha", "Kiran", "Sana",
    "Vikram", "Priya", "Rohit", "Neha", "Sahil", "Pooja", "Aditya", "Kavya", "Riya", "Dev",
]
LAST_NAMES = [
    "Nair", "Menon", "Iyer", "Sharma", "Pillai", "Gupta", "Kumar", "Singh", "Das", "Varma",
]


class Command(BaseCommand):
    help = "Seed demo data (departments, skills, 50 employees, 10 clients)."

    def handle(self, *args, **options):
        depts = {
            "IT & Technology": ["Frontend Developer", "Backend Developer", "Fullstack Developer", "DevOps Engineer"],
            "Design": ["UI Designer", "UX Designer", "Graphic Designer"],
            "Marketing": ["SEO Specialist", "Content Writer", "Social Media Manager"],
        }

        dept_objs = {}
        for dname, skills in depts.items():
            dept, _ = Department.objects.get_or_create(name=dname)
            dept_objs[dname] = dept
            for s in skills:
                Skill.objects.get_or_create(department=dept, name=s)

        # Admin user (optional)
        if not User.objects.filter(username="admin@jobmate.local").exists():
            admin_user = User.objects.create_superuser(
                username="admin@jobmate.local",
                email="admin@jobmate.local",
                password="admin123",
                first_name="JobMate",
                last_name="Admin",
            )
            admin_user.profile.role = UserRole.ADMIN
            admin_user.profile.save()
            self.stdout.write(self.style.SUCCESS("Created admin: admin@jobmate.local / admin123"))

        # Clients
        for i in range(10):
            email = f"client{i+1}@jobmate.local"
            if User.objects.filter(username=email).exists():
                continue
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            u = User.objects.create_user(username=email, email=email, password="client123", first_name=fn, last_name=ln)
            u.profile.role = UserRole.CLIENT
            u.profile.phone = f"98765{random.randint(10000,99999)}"
            u.profile.save()
            ClientProfile.objects.get_or_create(profile=u.profile, defaults={"company": f"{fn} {ln} Pvt Ltd"})

        # Employees
        skills = list(Skill.objects.select_related("department"))
        created = 0
        target = 50
        existing = EmployeeProfile.objects.count()
        while created + existing < target:
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            email = f"{fn.lower()}.{ln.lower()}{random.randint(100,999)}@jobmate.local"
            if User.objects.filter(username=email).exists():
                continue

            u = User.objects.create_user(username=email, email=email, password="employee123", first_name=fn, last_name=ln)
            u.profile.role = UserRole.EMPLOYEE
            u.profile.phone = f"98{random.randint(100000000,999999999)}"
            u.profile.save()

            sk = random.choice(skills)
            EmployeeProfile.objects.create(
                profile=u.profile,
                department=sk.department,
                skill=sk,
                title=sk.name,
                bio=f"Skilled {sk.name} available for short-term tasks.",
                hourly_rate=random.choice([250, 300, 350, 400, 500]),
                is_available=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seed complete. Employees: {EmployeeProfile.objects.count()}, Clients: {ClientProfile.objects.count()}"))
        self.stdout.write(self.style.SUCCESS("Demo logins: employee123 (employees), client123 (clients)"))
