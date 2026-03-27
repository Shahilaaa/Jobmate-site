"""
Seeds skills for all departments that are missing them.
Run on your existing database:

    python manage.py seed_skills

Safe to re-run — uses get_or_create so nothing is duplicated.
"""
from django.core.management.base import BaseCommand

DEPT_SKILLS = {
    "Information Technology": [
        "Web Development", "Backend Development", "Frontend Development",
        "Mobile Development", "Cloud & DevOps", "Database Administration",
        "Cybersecurity", "System Administration", "Network Engineering",
        "Software Testing / QA",
    ],
    "Software Development": [
        "Python", "JavaScript", "React", "Django", "Node.js",
        "Java", "Flutter", "iOS Development", "Android Development", "PHP",
    ],
    "Design": [
        "UI Design", "UX Design", "Graphic Design", "Logo Design",
        "Motion Graphics", "Figma", "Adobe XD", "Illustration",
    ],
    "Digital Marketing": [
        "SEO", "Social Media Marketing", "Google Ads",
        "Content Marketing", "Email Marketing", "Affiliate Marketing",
    ],
    "Data & Analytics": [
        "Data Analysis", "Machine Learning", "Power BI",
        "Tableau", "Excel Analytics", "Data Engineering",
    ],
    "IT Support": [
        "Networking", "System Administration", "Cybersecurity",
        "Cloud Computing", "DevOps", "Linux Administration",
    ],
    "Content Writing": [
        "Blog Writing", "Copywriting", "Technical Writing",
        "Script Writing", "Proofreading", "Resume Writing",
    ],
    "Admin & Operations": [
        "Project Management", "Virtual Assistant", "HR Operations",
        "Accounting", "Customer Support", "Data Entry",
    ],
    "Marketing": [
        "SEO", "Social Media Marketing", "Content Marketing",
        "Email Marketing", "Google Ads", "Brand Strategy",
        "Market Research", "Affiliate Marketing",
    ],
    "Finance & Accounting": [
        "Bookkeeping", "Financial Reporting", "Tax Preparation",
        "Payroll Processing", "Auditing", "Financial Planning",
        "Accounts Payable / Receivable",
    ],
    "Human Resources": [
        "Recruitment", "Onboarding", "Employee Relations",
        "Performance Management", "HR Policy", "Payroll & Benefits",
        "Training & Development",
    ],
    "Legal & Compliance": [
        "Contract Drafting", "Intellectual Property", "Corporate Law",
        "Regulatory Compliance", "Dispute Resolution", "Labour Law",
    ],
    "Engineering & Architecture": [
        "Civil Engineering", "Structural Engineering", "Mechanical Engineering",
        "Electrical Engineering", "Architecture & Design", "Project Supervision",
    ],
    "Education & Training": [
        "Corporate Training", "E-Learning Development", "Curriculum Design",
        "Academic Tutoring", "Instructional Design", "Workshop Facilitation",
    ],
    "Content & Media": [
        "Copywriting", "Video Production", "Podcast Editing",
        "Journalism", "Content Strategy", "Photography",
    ],
}


class Command(BaseCommand):
    help = "Seed skills for all departments (safe to re-run)"

    def handle(self, *args, **options):
        from pages.models import Department, Skill

        total_created = 0
        for dept_name, skills in DEPT_SKILLS.items():
            dept, dept_created = Department.objects.get_or_create(name=dept_name)
            if dept_created:
                self.stdout.write(f"  ➕ Created department: {dept_name}")
            created_count = 0
            for skill_name in skills:
                _, created = Skill.objects.get_or_create(department=dept, name=skill_name)
                if created:
                    created_count += 1
                    total_created += 1
            status = f"{created_count} new" if created_count else "all exist"
            self.stdout.write(f"  ✏️  {dept_name}: {status}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone — {total_created} new skills created."
        ))
        self.stdout.write(
            "The register page skill dropdowns will now populate correctly."
        )
