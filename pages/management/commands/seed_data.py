"""
Management command to seed initial data for JobMate.
Usage: python manage.py seed_data
       python manage.py seed_data --demo   (also creates demo users)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Seed JobMate database with departments, skills, and optional demo users"

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Also create demo users (admin, employee, client)")

    def handle(self, *args, **options):
        self.stdout.write("Seeding departments and skills...")
        self._seed_departments()

        if options["demo"]:
            self.stdout.write("Creating demo users...")
            self._seed_demo_users()

        self.stdout.write(self.style.SUCCESS("Done!"))

    def _seed_departments(self):
        from pages.models import Department, Skill

        departments_data = {
            "Software Development": {
                "description": (
                    "Our Software Development department brings together expert engineers, full-stack "
                    "developers, and mobile app specialists who build reliable, scalable digital products. "
                    "From web applications and APIs to iOS and Android apps, these professionals turn your "
                    "ideas into polished, production-ready software using the latest technologies."
                ),
                "skills": [
                    "Python", "JavaScript", "React", "Django", "Node.js",
                    "Java", "Flutter", "iOS Development", "Android Development", "PHP",
                ],
            },
            "Design": {
                "description": (
                    "The Design department is home to creative professionals who craft visually compelling "
                    "and intuitively usable experiences. Covering UI/UX design, brand identity, graphic "
                    "design, and motion graphics, our designers ensure your product looks exceptional and "
                    "communicates your brand with clarity and impact."
                ),
                "skills": [
                    "UI Design", "UX Design", "Graphic Design", "Logo Design",
                    "Motion Graphics", "Figma", "Adobe XD", "Illustration",
                ],
            },
            "Digital Marketing": {
                "description": (
                    "Our Digital Marketing department connects your business with the right audience through "
                    "data-driven strategies and creative campaigns. From SEO and pay-per-click advertising to "
                    "social media management, email automation, and content marketing, these specialists help "
                    "you grow visibility, generate quality leads, and increase revenue."
                ),
                "skills": [
                    "SEO", "Social Media Marketing", "Google Ads",
                    "Content Marketing", "Email Marketing", "Affiliate Marketing",
                ],
            },
            "Data & Analytics": {
                "description": (
                    "The Data & Analytics department provides expert professionals who transform raw data "
                    "into meaningful business insights. Covering data analysis, machine learning, business "
                    "intelligence, and data engineering, these specialists help organisations make confident, "
                    "evidence-based decisions and build the data infrastructure needed to scale."
                ),
                "skills": [
                    "Data Analysis", "Machine Learning", "Power BI",
                    "Tableau", "Excel Analytics", "Data Engineering",
                ],
            },
            "IT Support": {
                "description": (
                    "Our IT Support department provides reliable technical expertise to keep your systems "
                    "running smoothly. From network administration and cybersecurity to cloud computing, "
                    "DevOps, and Linux server management, these professionals safeguard your infrastructure "
                    "and ensure maximum uptime for your business operations."
                ),
                "skills": [
                    "Networking", "System Administration", "Cybersecurity",
                    "Cloud Computing", "DevOps", "Linux Administration",
                ],
            },
            "Content Writing": {
                "description": (
                    "The Content Writing department delivers clear, compelling written communication across "
                    "every format. Blog posts, website copy, technical documentation, scripts, and proofreading "
                    "— our writers combine research, creativity, and SEO awareness to produce content that "
                    "engages your audience and strengthens your brand voice."
                ),
                "skills": [
                    "Blog Writing", "Copywriting", "Technical Writing",
                    "Script Writing", "Proofreading", "Resume Writing",
                ],
            },
            "Admin & Operations": {
                "description": (
                    "Our Admin & Operations department provides skilled professionals who keep businesses "
                    "running efficiently behind the scenes. From project management and virtual assistance to "
                    "HR operations, bookkeeping, customer support, and data entry, these experts handle the "
                    "day-to-day tasks that let you focus on growth."
                ),
                "skills": [
                    "Project Management", "Virtual Assistant", "HR Operations",
                    "Accounting", "Customer Support", "Data Entry",
                ],
            },
            "Information Technology": {
                "description": (
                    "Our Information Technology department brings together expert software engineers, system "
                    "architects, and IT consultants who design, build, and maintain robust digital solutions. "
                    "From full-stack web applications and cloud infrastructure to cybersecurity and database "
                    "management, these professionals ensure your technology stack is reliable, scalable, and "
                    "future-ready."
                ),
                "skills": [
                    "Web Development", "Backend Development", "Frontend Development",
                    "Mobile Development", "Cloud & DevOps", "Database Administration",
                    "Cybersecurity", "System Administration", "Network Engineering",
                    "Software Testing / QA",
                ],
            },
            "Marketing": {
                "description": (
                    "Our Marketing department connects businesses with the right audience through data-driven "
                    "strategy and creative execution. From SEO and content marketing to social media campaigns, "
                    "email automation, and performance analytics, these professionals help you grow brand "
                    "awareness, generate qualified leads, and convert prospects into loyal customers."
                ),
                "skills": [
                    "SEO", "Social Media Marketing", "Content Marketing",
                    "Email Marketing", "Google Ads", "Brand Strategy",
                    "Market Research", "Affiliate Marketing",
                ],
            },
            "Finance & Accounting": {
                "description": (
                    "The Finance & Accounting department provides expert support across bookkeeping, financial "
                    "reporting, tax preparation, payroll processing, and strategic financial planning."
                ),
                "skills": [
                    "Bookkeeping", "Financial Reporting", "Tax Preparation",
                    "Payroll Processing", "Auditing", "Financial Planning",
                    "Accounts Payable / Receivable",
                ],
            },
            "Human Resources": {
                "description": (
                    "Our Human Resources department supports organisations in building and retaining "
                    "high-performing teams."
                ),
                "skills": [
                    "Recruitment", "Onboarding", "Employee Relations",
                    "Performance Management", "HR Policy", "Payroll & Benefits",
                    "Training & Development",
                ],
            },
            "Legal & Compliance": {
                "description": (
                    "The Legal & Compliance department offers access to qualified legal professionals and "
                    "compliance specialists who safeguard your business."
                ),
                "skills": [
                    "Contract Drafting", "Intellectual Property", "Corporate Law",
                    "Regulatory Compliance", "Dispute Resolution", "Labour Law",
                ],
            },
            "Engineering & Architecture": {
                "description": (
                    "The Engineering & Architecture department brings together civil engineers, structural "
                    "designers, mechanical engineers, and licensed architects."
                ),
                "skills": [
                    "Civil Engineering", "Structural Engineering", "Mechanical Engineering",
                    "Electrical Engineering", "Architecture & Design", "Project Supervision",
                ],
            },
            "Education & Training": {
                "description": (
                    "Our Education & Training department connects organisations with experienced trainers, "
                    "curriculum developers, and instructional designers."
                ),
                "skills": [
                    "Corporate Training", "E-Learning Development", "Curriculum Design",
                    "Academic Tutoring", "Instructional Design", "Workshop Facilitation",
                ],
            },
            "Content & Media": {
                "description": (
                    "Our Content & Media department covers every aspect of storytelling and communication."
                ),
                "skills": [
                    "Copywriting", "Video Production", "Podcast Editing",
                    "Journalism", "Content Strategy", "Photography",
                ],
            },
        }

        for dept_name, data in departments_data.items():
            dept, created = Department.objects.get_or_create(name=dept_name)
            # Always update description
            dept.description = data["description"]
            dept.save()
            status = "created" if created else "updated"
            self.stdout.write(f"  Department [{status}]: {dept_name}")
            for skill_name in data["skills"]:
                Skill.objects.get_or_create(department=dept, name=skill_name)

        from pages.models import Department as D, Skill as S
        self.stdout.write(
            self.style.SUCCESS(
                f"  Total: {D.objects.count()} departments, {S.objects.count()} skills"
            )
        )

    def _seed_demo_users(self):
        from pages.models import (
            Profile, UserRole, EmployeeProfile, ClientProfile,
            Department, Skill, TaskRequest, TaskStatus, Payment, PaymentStatus,
        )

        # --- Admin ---
        if not User.objects.filter(username="admin@jobmate.com").exists():
            admin = User.objects.create_superuser(
                username="admin@jobmate.com",
                email="admin@jobmate.com",
                password="Admin@1234",
                first_name="Admin",
                last_name="User",
            )
            try:
                p = admin.profile
                p.role = UserRole.ADMIN
                p.save()
            except Exception:
                Profile.objects.create(user=admin, role=UserRole.ADMIN)
            self.stdout.write(self.style.SUCCESS("  Admin: admin@jobmate.com / Admin@1234"))
        else:
            self.stdout.write("  Admin already exists")

        # --- Employee ---
        if not User.objects.filter(username="john@jobmate.com").exists():
            emp_user = User.objects.create_user(
                username="john@jobmate.com",
                email="john@jobmate.com",
                password="Emp@1234",
                first_name="John",
                last_name="Developer",
            )
            try:
                p = emp_user.profile
                p.role = UserRole.EMPLOYEE
                p.save()
            except Exception:
                p = Profile.objects.create(user=emp_user, role=UserRole.EMPLOYEE)

            dept = Department.objects.filter(name="Software Development").first()
            skill = Skill.objects.filter(name="Python").first()

            EmployeeProfile.objects.get_or_create(
                profile=emp_user.profile,
                defaults={
                    "department": dept,
                    "skill": skill,
                    "title": "Senior Python Developer",
                    "bio": "Experienced full-stack developer specializing in Python and Django. Available for freelance projects.",
                    "hourly_rate": 750,
                    "is_available": True,
                },
            )
            self.stdout.write(self.style.SUCCESS("  Employee: john@jobmate.com / Emp@1234"))
        else:
            self.stdout.write("  Demo employee already exists")

        # --- Client ---
        if not User.objects.filter(username="client@jobmate.com").exists():
            cli_user = User.objects.create_user(
                username="client@jobmate.com",
                email="client@jobmate.com",
                password="Client@1234",
                first_name="Sara",
                last_name="Smith",
            )
            try:
                p = cli_user.profile
                p.role = UserRole.CLIENT
                p.save()
            except Exception:
                p = Profile.objects.create(user=cli_user, role=UserRole.CLIENT)
            ClientProfile.objects.get_or_create(
                profile=cli_user.profile, defaults={"company": "TechCorp Ltd"}
            )
            self.stdout.write(self.style.SUCCESS("  Client: client@jobmate.com / Client@1234"))
        else:
            self.stdout.write("  Demo client already exists")

        # --- Sample Task ---
        try:
            emp_profile = EmployeeProfile.objects.filter(
                profile__user__username="john@jobmate.com"
            ).first()
            cli_profile = ClientProfile.objects.filter(
                profile__user__username="client@jobmate.com"
            ).first()
            skill = Skill.objects.filter(name="Python").first()
            dept = Department.objects.filter(name="Software Development").first()

            if emp_profile and cli_profile:
                task, created = TaskRequest.objects.get_or_create(
                    client=cli_profile,
                    employee=emp_profile,
                    title="Build REST API for mobile app",
                    defaults={
                        "description": "We need a secure REST API built with Django REST Framework for our mobile application.",
                        "department": dept,
                        "skill": skill,
                        "budget": 15000,
                        "status": TaskStatus.IN_PROGRESS,
                    },
                )
                if created:
                    Payment.objects.create(
                        task=task,
                        client=cli_profile,
                        amount=15000,
                        status=PaymentStatus.PENDING,
                    )
                    self.stdout.write(self.style.SUCCESS("  Sample task and payment created"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Could not create sample task: {e}"))
