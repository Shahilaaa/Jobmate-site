"""
One-shot command to add descriptions to all departments.
Run this on an existing database:

    python manage.py seed_descriptions

Safe to run multiple times — always overwrites with latest descriptions.
"""
from django.core.management.base import BaseCommand


DEPARTMENTS = [
    (
        "Software Development",
        "Our Software Development department brings together expert engineers, full-stack "
        "developers, and mobile app specialists who build reliable, scalable digital products. "
        "From web applications and APIs to iOS and Android apps, these professionals turn your "
        "ideas into polished, production-ready software using the latest technologies."
    ),
    (
        "Design",
        "The Design department is home to creative professionals who craft visually compelling "
        "and intuitively usable experiences. Covering UI/UX design, brand identity, graphic "
        "design, and motion graphics, our designers ensure your product looks exceptional and "
        "communicates your brand with clarity and impact."
    ),
    (
        "Digital Marketing",
        "Our Digital Marketing department connects your business with the right audience through "
        "data-driven strategies and creative campaigns. From SEO and pay-per-click advertising to "
        "social media management, email automation, and content marketing, these specialists help "
        "you grow visibility, generate quality leads, and increase revenue."
    ),
    (
        "Data & Analytics",
        "The Data & Analytics department provides expert professionals who transform raw data "
        "into meaningful business insights. Covering data analysis, machine learning, business "
        "intelligence, and data engineering, these specialists help organisations make confident, "
        "evidence-based decisions and build the data infrastructure needed to scale."
    ),
    (
        "IT Support",
        "Our IT Support department provides reliable technical expertise to keep your systems "
        "running smoothly. From network administration and cybersecurity to cloud computing, "
        "DevOps, and Linux server management, these professionals safeguard your infrastructure "
        "and ensure maximum uptime for your business operations."
    ),
    (
        "Content Writing",
        "The Content Writing department delivers clear, compelling written communication across "
        "every format. Blog posts, website copy, technical documentation, scripts, and proofreading "
        "— our writers combine research, creativity, and SEO awareness to produce content that "
        "engages your audience and strengthens your brand voice."
    ),
    (
        "Admin & Operations",
        "Our Admin & Operations department provides skilled professionals who keep businesses "
        "running efficiently behind the scenes. From project management and virtual assistance to "
        "HR operations, bookkeeping, customer support, and data entry, these experts handle the "
        "day-to-day tasks that let you focus on growth."
    ),
    (
        "Information Technology",
        "Our Information Technology department brings together expert software engineers, system "
        "architects, and IT consultants who design, build, and maintain robust digital solutions. "
        "From full-stack web applications and cloud infrastructure to cybersecurity and database "
        "management, these professionals ensure your technology stack is reliable, scalable, and "
        "future-ready."
    ),
    (
        "Finance & Accounting",
        "The Finance & Accounting department provides expert support across bookkeeping, financial "
        "reporting, tax preparation, payroll processing, and strategic financial planning. Whether "
        "you need ongoing accounts management or a one-time audit, our finance professionals ensure "
        "your numbers are accurate, compliant, and aligned with your business goals."
    ),
    (
        "Human Resources",
        "Our Human Resources department supports organisations in building and retaining "
        "high-performing teams. Services include recruitment and talent acquisition, onboarding, "
        "employee relations, performance management, HR policy development, and labour law "
        "compliance. These professionals help create workplace cultures where people thrive."
    ),
    (
        "Legal & Compliance",
        "The Legal & Compliance department offers access to qualified legal professionals and "
        "compliance specialists who safeguard your business. From contract drafting and intellectual "
        "property protection to regulatory compliance, corporate governance, and dispute resolution, "
        "these experts ensure you operate within the law and minimise legal risk at every stage."
    ),
    (
        "Engineering & Architecture",
        "The Engineering & Architecture department brings together civil engineers, structural "
        "designers, mechanical engineers, and licensed architects to support construction, "
        "infrastructure, and product development projects. These professionals provide technical "
        "expertise from initial concept and feasibility studies through to detailed design, "
        "project supervision, and final delivery."
    ),
    (
        "Education & Training",
        "Our Education & Training department connects organisations with experienced trainers, "
        "curriculum developers, instructional designers, and subject-matter experts. Whether you "
        "need corporate training programmes, e-learning content, professional development workshops, "
        "or academic tutoring, these specialists design and deliver engaging learning experiences "
        "that drive real skill growth."
    ),
]


class Command(BaseCommand):
    help = "Seed descriptions for all departments (safe to re-run)"

    def handle(self, *args, **options):
        from pages.models import Department

        updated = 0
        created = 0

        for name, description in DEPARTMENTS:
            dept, was_created = Department.objects.get_or_create(name=name)
            dept.description = description
            dept.save()
            if was_created:
                created += 1
                self.stdout.write(f"  ➕ Created: {name}")
            else:
                updated += 1
                self.stdout.write(f"  ✏️  Updated: {name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone — {created} created, {updated} updated."
        ))
        self.stdout.write(
            "Refresh the Roles & Skills page to see descriptions."
        )
