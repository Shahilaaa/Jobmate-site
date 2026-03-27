"""
Squashed migration — replaces all previous migrations (0001–0026).
Run on a fresh database: python manage.py migrate
This creates all tables AND seeds the initial data in one step.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


# ─────────────────────────────────────────────────────────────────────────────
#  SEED DATA FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

DEPARTMENTS_DATA = [
    ("Software Development", "Our Software Development department brings together expert engineers, full-stack developers, and mobile app specialists who build reliable, scalable digital products. From web applications and APIs to iOS and Android apps, these professionals turn your ideas into polished, production-ready software using the latest technologies."),
    ("Design", "The Design department is home to creative professionals who craft visually compelling and intuitively usable experiences. Covering UI/UX design, brand identity, graphic design, and motion graphics, our designers ensure your product looks exceptional and communicates your brand with clarity and impact."),
    ("Digital Marketing", "Our Digital Marketing department connects your business with the right audience through data-driven strategies and creative campaigns. From SEO and pay-per-click advertising to social media management, email automation, and content marketing, these specialists help you grow visibility, generate quality leads, and increase revenue."),
    ("Data & Analytics", "The Data & Analytics department provides expert professionals who transform raw data into meaningful business insights. Covering data analysis, machine learning, business intelligence, and data engineering, these specialists help organisations make confident, evidence-based decisions and build the data infrastructure needed to scale."),
    ("IT Support", "Our IT Support department provides reliable technical expertise to keep your systems running smoothly. From network administration and cybersecurity to cloud computing, DevOps, and Linux server management, these professionals safeguard your infrastructure and ensure maximum uptime for your business operations."),
    ("Content Writing", "The Content Writing department delivers clear, compelling written communication across every format. Blog posts, website copy, technical documentation, scripts, and proofreading — our writers combine research, creativity, and SEO awareness to produce content that engages your audience and strengthens your brand voice."),
    ("Admin & Operations", "Our Admin & Operations department provides skilled professionals who keep businesses running efficiently behind the scenes. From project management and virtual assistance to HR operations, bookkeeping, customer support, and data entry, these experts handle the day-to-day tasks that let you focus on growth."),
    ("Information Technology", "Our Information Technology department brings together expert software engineers, system architects, and IT consultants who design, build, and maintain robust digital solutions. From full-stack web applications and cloud infrastructure to cybersecurity and database management, these professionals ensure your technology stack is reliable, scalable, and future-ready."),
    ("Finance & Accounting", "The Finance & Accounting department provides expert support across bookkeeping, financial reporting, tax preparation, payroll processing, and strategic financial planning. Whether you need ongoing accounts management or a one-time audit, our finance professionals ensure your numbers are accurate, compliant, and aligned with your business goals."),
    ("Human Resources", "Our Human Resources department supports organisations in building and retaining high-performing teams. Services include recruitment and talent acquisition, onboarding, employee relations, performance management, HR policy development, and labour law compliance. These professionals help create workplace cultures where people thrive."),
    ("Legal & Compliance", "The Legal & Compliance department offers access to qualified legal professionals and compliance specialists who safeguard your business. From contract drafting and intellectual property protection to regulatory compliance, corporate governance, and dispute resolution, these experts ensure you operate within the law and minimise legal risk at every stage."),
    ("Engineering & Architecture", "The Engineering & Architecture department brings together civil engineers, structural designers, mechanical engineers, and licensed architects to support construction, infrastructure, and product development projects. These professionals provide technical expertise from initial concept and feasibility studies through to detailed design, project supervision, and final delivery."),
    ("Education & Training", "Our Education & Training department connects organisations with experienced trainers, curriculum developers, instructional designers, and subject-matter experts. Whether you need corporate training programmes, e-learning content, professional development workshops, or academic tutoring, these specialists design and deliver engaging learning experiences that drive real skill growth."),
]

DEPT_SKILLS = {
    "Software Development": ["Web Development", "Backend Development", "Frontend Development", "Mobile Development", "Cloud & DevOps", "Database Administration", "Software Testing / QA"],
    "Design": ["UI/UX Design", "Graphic Design", "Brand Identity", "Motion Graphics", "Illustration", "Figma / Sketch", "Adobe Creative Suite"],
    "Digital Marketing": ["SEO", "Social Media Marketing", "Content Marketing", "Email Marketing", "Google Ads", "Brand Strategy", "Market Research", "Affiliate Marketing"],
    "Data & Analytics": ["Data Analysis", "Machine Learning", "Business Intelligence", "Data Engineering", "Python / R", "SQL", "Tableau / Power BI"],
    "IT Support": ["Network Administration", "Cybersecurity", "Cloud Computing", "DevOps", "Linux Server Management", "Technical Support", "IT Infrastructure"],
    "Content Writing": ["Blog Writing", "Copywriting", "Technical Writing", "Script Writing", "Proofreading & Editing", "SEO Writing", "Content Strategy"],
    "Admin & Operations": ["Project Management", "Virtual Assistance", "HR Operations", "Bookkeeping", "Customer Support", "Data Entry", "Operations Management"],
    "Information Technology": ["Web Development", "Backend Development", "Frontend Development", "Mobile Development", "Cloud & DevOps", "Database Administration", "Cybersecurity", "System Administration", "Network Engineering", "Software Testing / QA"],
    "Finance & Accounting": ["Bookkeeping", "Financial Reporting", "Tax Preparation", "Payroll Processing", "Auditing", "Financial Planning", "Accounts Payable / Receivable"],
    "Human Resources": ["Recruitment", "Onboarding", "Employee Relations", "Performance Management", "HR Policy", "Payroll & Benefits", "Training & Development"],
    "Legal & Compliance": ["Contract Drafting", "Intellectual Property", "Corporate Law", "Regulatory Compliance", "Dispute Resolution", "Labour Law"],
    "Engineering & Architecture": ["Civil Engineering", "Structural Engineering", "Mechanical Engineering", "Electrical Engineering", "Architecture & Design", "Project Supervision"],
    "Education & Training": ["Corporate Training", "E-Learning Development", "Curriculum Design", "Academic Tutoring", "Instructional Design", "Workshop Facilitation"],
    "Marketing": ["SEO", "Social Media Marketing", "Content Marketing", "Email Marketing", "Google Ads", "Brand Strategy", "Market Research", "Affiliate Marketing"],
    "Content & Media": ["Copywriting", "Video Production", "Podcast Editing", "Journalism", "Content Strategy", "Photography"],
}

SUPPORT_CARDS = [
    ("How It Works", "Browse our pool of vetted professionals, post your task with a budget, and get matched instantly. Our platform handles everything from task assignment to final delivery.", 0),
    ("Fast Turnaround", "Most tasks are picked up within 24 hours. Our employees are available full-time and committed to meeting your deadlines without compromising on quality.", 1),
    ("Secure Payments", "Payments are only released once you mark the work as complete. Your money is held safely until you're satisfied — zero risk to clients.", 2),
]

FAQS_DATA = [
    ("How do I post a new task?", "Log in to your dashboard, click 'Add New Task' from the Works page, fill in the title, description, budget and deadline, then submit. An employee will be assigned shortly.", 0),
    ("How long does it take to find an employee?", "Most tasks are matched within 24–48 hours. Complex or specialised tasks may take slightly longer as we ensure the best skill-match for your project.", 1),
    ("Can I communicate with my assigned employee?", "Yes. Once a task is accepted you can open a direct chat with the employee from the Works page. Real-time messaging is available from any page in your dashboard.", 2),
    ("How do I download completed work?", "When an employee submits their work you will see a 'Work Submitted' badge on the task card. Click 'Download Work File', review the deliverable, then mark the task as Complete.", 3),
    ("What payment methods are supported?", "Payments are recorded automatically when a task is marked complete. Bank transfer and card options are available — details are shown on the Payments page.", 4),
    ("How do I raise a support ticket?", "Scroll to the bottom of this Support page and fill in the 'Submit a Support Ticket' form. Our team reviews all tickets within one business day.", 5),
    ("Can I edit or delete a task after posting?", "Yes, as long as the task is still in 'Pending' status. Go to Works, find the task, and use the Edit or Delete buttons. Once accepted by an employee, edits are locked.", 6),
]



def create_tables_if_needed(apps, schema_editor):
    """
    Create all tables only if they don't already exist.
    Works on fresh databases AND existing ones — no manual commands needed.
    """
    from django.db import connection

    def table_exists(table_name):
        with connection.cursor() as cursor:
            tables = connection.introspection.get_table_list(cursor)
            return any(t.name == table_name for t in tables)

    # Map of table_name → CREATE TABLE SQL (PostgreSQL compatible)
    CREATE_SQLS = [
        ("pages_department", """
            CREATE TABLE pages_department (
                id bigserial PRIMARY KEY,
                name varchar(120) UNIQUE NOT NULL,
                description text NOT NULL DEFAULT \'\',
                image varchar(100)
            )"""),
        ("pages_skill", """
            CREATE TABLE pages_skill (
                id bigserial PRIMARY KEY,
                name varchar(120) NOT NULL,
                department_id bigint NOT NULL REFERENCES pages_department(id) ON DELETE CASCADE,
                UNIQUE(department_id, name)
            )"""),
        ("pages_profile", """
            CREATE TABLE pages_profile (
                id bigserial PRIMARY KEY,
                role varchar(20) NOT NULL DEFAULT \'client\',
                phone varchar(20) NOT NULL DEFAULT \'\',
                bio text NOT NULL DEFAULT \'\',
                user_id integer NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE
            )"""),
        ("pages_employeeprofile", """
            CREATE TABLE pages_employeeprofile (
                id bigserial PRIMARY KEY,
                title varchar(120) NOT NULL DEFAULT \'\',
                bio text NOT NULL DEFAULT \'\',
                hourly_rate numeric(10,2) NOT NULL DEFAULT 0,
                is_available boolean NOT NULL DEFAULT true,
                profile_image varchar(100),
                background_image varchar(100),
                cv varchar(100),
                approval_status varchar(20) NOT NULL DEFAULT \'pending\',
                approved_at timestamptz,
                rejected_reason text NOT NULL DEFAULT \'\',
                department_id bigint REFERENCES pages_department(id) ON DELETE SET NULL,
                profile_id bigint NOT NULL UNIQUE REFERENCES pages_profile(id) ON DELETE CASCADE,
                skill_id bigint REFERENCES pages_skill(id) ON DELETE SET NULL
            )"""),
        ("pages_clientprofile", """
            CREATE TABLE pages_clientprofile (
                id bigserial PRIMARY KEY,
                company varchar(160) NOT NULL DEFAULT \'\',
                profile_image varchar(100),
                background_image varchar(100),
                national_id varchar(100),
                approval_status varchar(20) NOT NULL DEFAULT \'pending\',
                approved_at timestamptz,
                rejected_reason text NOT NULL DEFAULT \'\',
                profile_id bigint NOT NULL UNIQUE REFERENCES pages_profile(id) ON DELETE CASCADE
            )"""),
        ("pages_testimonial", """
            CREATE TABLE pages_testimonial (
                id bigserial PRIMARY KEY,
                author_name varchar(120) NOT NULL,
                author_title varchar(120) NOT NULL DEFAULT \'\',
                text text NOT NULL,
                rating smallint NOT NULL DEFAULT 5,
                author_image varchar(100),
                date date NOT NULL,
                show_on_homepage boolean NOT NULL DEFAULT true,
                created_at timestamptz NOT NULL DEFAULT now(),
                employee_id bigint NOT NULL REFERENCES pages_employeeprofile(id) ON DELETE CASCADE
            )"""),
        ("pages_accreditation", """
            CREATE TABLE pages_accreditation (
                id bigserial PRIMARY KEY,
                title varchar(200) NOT NULL,
                issuer varchar(120) NOT NULL DEFAULT \'\',
                image varchar(100),
                date_issued date,
                created_at timestamptz NOT NULL DEFAULT now(),
                employee_id bigint NOT NULL REFERENCES pages_employeeprofile(id) ON DELETE CASCADE
            )"""),
        ("pages_portfolio", """
            CREATE TABLE pages_portfolio (
                id bigserial PRIMARY KEY,
                title varchar(200) NOT NULL,
                description text NOT NULL DEFAULT \'\',
                link varchar(200) NOT NULL DEFAULT \'\',
                image varchar(100),
                date date,
                created_at timestamptz NOT NULL DEFAULT now(),
                employee_id bigint NOT NULL REFERENCES pages_employeeprofile(id) ON DELETE CASCADE
            )"""),
        ("pages_taskrequest", """
            CREATE TABLE pages_taskrequest (
                id bigserial PRIMARY KEY,
                title varchar(160) NOT NULL,
                description text NOT NULL,
                budget numeric(12,2) NOT NULL DEFAULT 0,
                status varchar(20) NOT NULL DEFAULT \'pending\',
                start_date date,
                end_date date,
                created_at timestamptz NOT NULL DEFAULT now(),
                client_id bigint NOT NULL REFERENCES pages_clientprofile(id) ON DELETE CASCADE,
                department_id bigint REFERENCES pages_department(id) ON DELETE SET NULL,
                employee_id bigint NOT NULL REFERENCES pages_employeeprofile(id) ON DELETE CASCADE,
                skill_id bigint REFERENCES pages_skill(id) ON DELETE SET NULL
            )"""),
        ("pages_workupdate", """
            CREATE TABLE pages_workupdate (
                id bigserial PRIMARY KEY,
                note text NOT NULL DEFAULT \'\',
                hours_worked numeric(8,2) NOT NULL DEFAULT 0,
                attachment varchar(100),
                work_file varchar(100),
                submitted_at timestamptz NOT NULL DEFAULT now(),
                employee_id bigint NOT NULL REFERENCES pages_employeeprofile(id) ON DELETE CASCADE,
                task_id bigint NOT NULL REFERENCES pages_taskrequest(id) ON DELETE CASCADE
            )"""),
        ("pages_payment", """
            CREATE TABLE pages_payment (
                id bigserial PRIMARY KEY,
                amount numeric(12,2) NOT NULL,
                admin_commission numeric(12,2) NOT NULL DEFAULT 0,
                employee_payout numeric(12,2) NOT NULL DEFAULT 0,
                status varchar(20) NOT NULL DEFAULT \'pending\',
                method varchar(50) NOT NULL DEFAULT \'\',
                transaction_id varchar(100) NOT NULL DEFAULT \'\',
                razorpay_order_id varchar(64) NOT NULL DEFAULT \'\',
                razorpay_payment_id varchar(64) NOT NULL DEFAULT \'\',
                razorpay_signature varchar(128) NOT NULL DEFAULT \'\',
                paid_at timestamptz,
                client_id bigint NOT NULL REFERENCES pages_clientprofile(id) ON DELETE CASCADE,
                task_id bigint NOT NULL UNIQUE REFERENCES pages_taskrequest(id) ON DELETE CASCADE
            )"""),
        ("pages_supportticket", """
            CREATE TABLE pages_supportticket (
                id bigserial PRIMARY KEY,
                subject varchar(160) NOT NULL,
                message text NOT NULL,
                status varchar(20) NOT NULL DEFAULT \'open\',
                created_at timestamptz NOT NULL DEFAULT now(),
                created_by_id integer NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
            )"""),
        ("pages_notification", """
            CREATE TABLE pages_notification (
                id bigserial PRIMARY KEY,
                title varchar(160) NOT NULL,
                message text NOT NULL DEFAULT \'\',
                link varchar(500) NOT NULL DEFAULT \'\',
                is_read boolean NOT NULL DEFAULT false,
                created_at timestamptz NOT NULL DEFAULT now(),
                user_id integer NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
            )"""),
        ("pages_conversation", """
            CREATE TABLE pages_conversation (
                id bigserial PRIMARY KEY,
                created_at timestamptz NOT NULL DEFAULT now(),
                client_id bigint NOT NULL REFERENCES pages_clientprofile(id) ON DELETE CASCADE,
                employee_id bigint NOT NULL REFERENCES pages_employeeprofile(id) ON DELETE CASCADE,
                UNIQUE(client_id, employee_id)
            )"""),
        ("pages_chatmessage", """
            CREATE TABLE pages_chatmessage (
                id bigserial PRIMARY KEY,
                text text NOT NULL DEFAULT \'\',
                attachment varchar(100),
                created_at timestamptz NOT NULL DEFAULT now(),
                conversation_id bigint NOT NULL REFERENCES pages_conversation(id) ON DELETE CASCADE,
                sender_id integer NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
            )"""),
        ("pages_enquiry", """
            CREATE TABLE pages_enquiry (
                id bigserial PRIMARY KEY,
                name varchar(120) NOT NULL,
                email varchar(254) NOT NULL,
                service varchar(120) NOT NULL DEFAULT \'\',
                message text NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )"""),
        ("pages_supportcard", """
            CREATE TABLE pages_supportcard (
                id bigserial PRIMARY KEY,
                title varchar(120) NOT NULL,
                body text NOT NULL,
                "order" smallint NOT NULL DEFAULT 0,
                is_active boolean NOT NULL DEFAULT true
            )"""),
        ("pages_faq", """
            CREATE TABLE pages_faq (
                id bigserial PRIMARY KEY,
                question varchar(300) NOT NULL,
                answer text NOT NULL,
                "order" smallint NOT NULL DEFAULT 0,
                is_active boolean NOT NULL DEFAULT true
            )"""),
        ("pages_project", """
            CREATE TABLE pages_project (
                id bigserial PRIMARY KEY,
                title varchar(200) NOT NULL,
                description text NOT NULL,
                budget numeric(12,2) NOT NULL DEFAULT 0,
                deadline timestamptz,
                status varchar(20) NOT NULL DEFAULT \'active\',
                work_file varchar(100),
                work_note text NOT NULL DEFAULT \'\',
                work_submitted_at timestamptz,
                completed_at timestamptz,
                created_at timestamptz NOT NULL DEFAULT now(),
                assigned_to_id bigint REFERENCES pages_employeeprofile(id) ON DELETE SET NULL,
                client_id bigint NOT NULL REFERENCES pages_clientprofile(id) ON DELETE CASCADE,
                department_id bigint REFERENCES pages_department(id) ON DELETE SET NULL,
                skill_id bigint REFERENCES pages_skill(id) ON DELETE SET NULL
            )"""),
        ("pages_projectapplication", """
            CREATE TABLE pages_projectapplication (
                id bigserial PRIMARY KEY,
                message text NOT NULL DEFAULT \'\',
                status varchar(20) NOT NULL DEFAULT \'pending\',
                applied_at timestamptz NOT NULL DEFAULT now(),
                employee_id bigint NOT NULL REFERENCES pages_employeeprofile(id) ON DELETE CASCADE,
                project_id bigint NOT NULL REFERENCES pages_project(id) ON DELETE CASCADE,
                UNIQUE(project_id, employee_id)
            )"""),
        ("pages_projectpayment", """
            CREATE TABLE pages_projectpayment (
                id bigserial PRIMARY KEY,
                amount numeric(12,2) NOT NULL DEFAULT 0,
                admin_commission numeric(12,2) NOT NULL DEFAULT 0,
                employee_payout numeric(12,2) NOT NULL DEFAULT 0,
                status varchar(20) NOT NULL DEFAULT \'pending\',
                method varchar(50) NOT NULL DEFAULT \'\',
                transaction_id varchar(100) NOT NULL DEFAULT \'\',
                razorpay_order_id varchar(64) NOT NULL DEFAULT \'\',
                razorpay_payment_id varchar(64) NOT NULL DEFAULT \'\',
                razorpay_signature varchar(128) NOT NULL DEFAULT \'\',
                created_at timestamptz NOT NULL DEFAULT now(),
                client_id bigint NOT NULL REFERENCES pages_clientprofile(id) ON DELETE CASCADE,
                employee_id bigint NOT NULL REFERENCES pages_employeeprofile(id) ON DELETE CASCADE,
                project_id bigint NOT NULL UNIQUE REFERENCES pages_project(id) ON DELETE CASCADE
            )"""),
        ("pages_bankdetail", """
            CREATE TABLE pages_bankdetail (
                id bigserial PRIMARY KEY,
                account_holder varchar(160) NOT NULL,
                account_number varchar(30) NOT NULL,
                ifsc_code varchar(20) NOT NULL,
                bank_name varchar(120) NOT NULL,
                branch_name varchar(160) NOT NULL DEFAULT \'\',
                account_type varchar(20) NOT NULL DEFAULT \'savings\',
                razorpay_contact_id varchar(64) NOT NULL DEFAULT \'\',
                razorpay_fund_account_id varchar(64) NOT NULL DEFAULT \'\',
                is_verified boolean NOT NULL DEFAULT false,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                user_id integer NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE
            )"""),
    ]

    with connection.cursor() as cursor:
        for table_name, sql in CREATE_SQLS:
            if not table_exists(table_name):
                cursor.execute(sql.replace("\'", "'"))


def seed_all(apps, schema_editor):
    """Delegate to standalone seed module so it can also be run via management command."""
    from pages.squashed_seed import run_seed
    run_seed()


def unseed_all(apps, schema_editor):
    pass  # Wipe is handled inside run_seed() — irreversible


class Migration(migrations.Migration):
    """Single squashed migration — full schema + seed data. Replaces 0001–0026."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # state_operations: registers all models in Django's migration state
            # so apps.get_model() works in RunPython functions below
            state_operations=[
                migrations.CreateModel(name="Department", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("name", models.CharField(max_length=120, unique=True)),
                    ("description", models.TextField(blank=True, default="")),
                    ("image", models.ImageField(blank=True, null=True, upload_to="departments/")),
                ]),
                migrations.CreateModel(name="Skill", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("name", models.CharField(max_length=120)),
                    ("department", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skills", to="pages.department")),
                ], options={"unique_together": {("department", "name")}}),
                migrations.CreateModel(name="Profile", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("role", models.CharField(choices=[("admin","Admin"),("employee","Employee"),("client","Client")], default="client", max_length=20)),
                    ("phone", models.CharField(blank=True, max_length=20)),
                    ("bio", models.TextField(blank=True)),
                    ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ]),
                migrations.CreateModel(name="EmployeeProfile", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("title", models.CharField(blank=True, max_length=120)),
                    ("bio", models.TextField(blank=True)),
                    ("hourly_rate", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                    ("is_available", models.BooleanField(default=True)),
                    ("profile_image", models.ImageField(blank=True, null=True, upload_to="profiles/")),
                    ("background_image", models.ImageField(blank=True, null=True, upload_to="backgrounds/")),
                    ("cv", models.FileField(blank=True, null=True, upload_to="cvs/")),
                    ("approval_status", models.CharField(choices=[("pending","Pending"),("approved","Approved"),("rejected","Rejected")], default="pending", max_length=20)),
                    ("approved_at", models.DateTimeField(blank=True, null=True)),
                    ("rejected_reason", models.TextField(blank=True)),
                    ("department", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="pages.department")),
                    ("profile", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="employee", to="pages.profile")),
                    ("skill", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="pages.skill")),
                ]),
                migrations.CreateModel(name="ClientProfile", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("company", models.CharField(blank=True, max_length=160)),
                    ("profile_image", models.ImageField(blank=True, null=True, upload_to="profiles/")),
                    ("background_image", models.ImageField(blank=True, null=True, upload_to="backgrounds/")),
                    ("national_id", models.FileField(blank=True, null=True, upload_to="national_ids/")),
                    ("approval_status", models.CharField(choices=[("pending","Pending"),("approved","Approved"),("rejected","Rejected")], default="pending", max_length=20)),
                    ("approved_at", models.DateTimeField(blank=True, null=True)),
                    ("rejected_reason", models.TextField(blank=True)),
                    ("profile", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="client", to="pages.profile")),
                ]),
                migrations.CreateModel(name="Testimonial", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("author_name", models.CharField(max_length=120)),
                    ("author_title", models.CharField(blank=True, max_length=120)),
                    ("text", models.TextField()),
                    ("rating", models.PositiveSmallIntegerField(default=5)),
                    ("author_image", models.ImageField(blank=True, null=True, upload_to="testimonials/")),
                    ("date", models.DateField()),
                    ("show_on_homepage", models.BooleanField(default=True)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="testimonials", to="pages.employeeprofile")),
                ], options={"ordering": ["-date"]}),
                migrations.CreateModel(name="Accreditation", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("title", models.CharField(max_length=200)),
                    ("issuer", models.CharField(blank=True, max_length=120)),
                    ("image", models.ImageField(blank=True, null=True, upload_to="accreditations/")),
                    ("date_issued", models.DateField(blank=True, null=True)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="accreditations", to="pages.employeeprofile")),
                ], options={"ordering": ["-date_issued"]}),
                migrations.CreateModel(name="Portfolio", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("title", models.CharField(max_length=200)),
                    ("description", models.TextField(blank=True)),
                    ("link", models.URLField(blank=True)),
                    ("image", models.ImageField(blank=True, null=True, upload_to="portfolio/")),
                    ("date", models.DateField(blank=True, null=True)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="portfolio_items", to="pages.employeeprofile")),
                ], options={"ordering": ["-date", "-created_at"]}),
                migrations.CreateModel(name="TaskRequest", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("title", models.CharField(max_length=160)),
                    ("description", models.TextField()),
                    ("budget", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                    ("status", models.CharField(choices=[("pending","Pending"),("accepted","Accepted"),("in_progress","In Progress"),("submitted","Submitted"),("completed","Completed"),("rejected","Rejected")], default="pending", max_length=20)),
                    ("start_date", models.DateField(blank=True, null=True)),
                    ("end_date", models.DateField(blank=True, null=True)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="pages.clientprofile")),
                    ("department", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="pages.department")),
                    ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="pages.employeeprofile")),
                    ("skill", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="pages.skill")),
                ]),
                migrations.CreateModel(name="WorkUpdate", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("note", models.TextField(blank=True)),
                    ("hours_worked", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                    ("attachment", models.FileField(blank=True, null=True, upload_to="work/")),
                    ("work_file", models.FileField(blank=True, null=True, upload_to="work_deliverables/")),
                    ("submitted_at", models.DateTimeField(auto_now_add=True)),
                    ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="pages.employeeprofile")),
                    ("task", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="work_updates", to="pages.taskrequest")),
                ]),
                migrations.CreateModel(name="Payment", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                    ("admin_commission", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                    ("employee_payout", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                    ("status", models.CharField(choices=[("pending","Pending"),("paid","Paid"),("failed","Failed")], default="pending", max_length=20)),
                    ("method", models.CharField(blank=True, max_length=50)),
                    ("transaction_id", models.CharField(blank=True, max_length=100)),
                    ("razorpay_order_id", models.CharField(blank=True, max_length=64)),
                    ("razorpay_payment_id", models.CharField(blank=True, max_length=64)),
                    ("razorpay_signature", models.CharField(blank=True, max_length=128)),
                    ("paid_at", models.DateTimeField(blank=True, null=True)),
                    ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="pages.clientprofile")),
                    ("task", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment", to="pages.taskrequest")),
                ]),
                migrations.CreateModel(name="SupportTicket", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("subject", models.CharField(max_length=160)),
                    ("message", models.TextField()),
                    ("status", models.CharField(choices=[("open","Open"),("in_progress","In Progress"),("closed","Closed")], default="open", max_length=20)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ]),
                migrations.CreateModel(name="Notification", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("title", models.CharField(max_length=160)),
                    ("message", models.TextField(blank=True)),
                    ("link", models.CharField(blank=True, max_length=500)),
                    ("is_read", models.BooleanField(default=False)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
                ]),
                migrations.CreateModel(name="Conversation", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="conversations", to="pages.clientprofile")),
                    ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="conversations", to="pages.employeeprofile")),
                ], options={"unique_together": {("client", "employee")}}),
                migrations.CreateModel(name="ChatMessage", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("text", models.TextField(blank=True)),
                    ("attachment", models.FileField(blank=True, null=True, upload_to="chat_attachments/")),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="pages.conversation")),
                    ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ]),
                migrations.CreateModel(name="Enquiry", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("name", models.CharField(max_length=120)),
                    ("email", models.EmailField()),
                    ("service", models.CharField(blank=True, max_length=120)),
                    ("message", models.TextField()),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                ], options={"ordering": ["-created_at"], "verbose_name_plural": "Enquiries"}),
                migrations.CreateModel(name="SupportCard", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("title", models.CharField(max_length=120)),
                    ("body", models.TextField()),
                    ("order", models.PositiveSmallIntegerField(default=0)),
                    ("is_active", models.BooleanField(default=True)),
                ], options={"ordering": ["order", "id"]}),
                migrations.CreateModel(name="FAQ", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("question", models.CharField(max_length=300)),
                    ("answer", models.TextField()),
                    ("order", models.PositiveSmallIntegerField(default=0)),
                    ("is_active", models.BooleanField(default=True)),
                ], options={"ordering": ["order", "id"], "verbose_name": "FAQ", "verbose_name_plural": "FAQs"}),
                migrations.CreateModel(name="Project", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("title", models.CharField(max_length=200)),
                    ("description", models.TextField()),
                    ("budget", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                    ("deadline", models.DateTimeField(blank=True, null=True)),
                    ("status", models.CharField(choices=[("active","Active"),("assigned","Assigned"),("work_submitted","Work Submitted"),("completed","Completed"),("closed","Closed")], default="active", max_length=20)),
                    ("work_file", models.FileField(blank=True, null=True, upload_to="project_deliverables/")),
                    ("work_note", models.TextField(blank=True)),
                    ("work_submitted_at", models.DateTimeField(blank=True, null=True)),
                    ("completed_at", models.DateTimeField(blank=True, null=True)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_projects", to="pages.employeeprofile")),
                    ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="projects", to="pages.clientprofile")),
                    ("department", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="pages.department")),
                    ("skill", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="pages.skill")),
                ], options={"ordering": ["-created_at"]}),
                migrations.CreateModel(name="ProjectApplication", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("message", models.TextField(blank=True)),
                    ("status", models.CharField(choices=[("pending","Pending"),("accepted","Accepted"),("rejected","Rejected")], default="pending", max_length=20)),
                    ("applied_at", models.DateTimeField(auto_now_add=True)),
                    ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_applications", to="pages.employeeprofile")),
                    ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="pages.project")),
                ], options={"ordering": ["-applied_at"], "unique_together": {("project", "employee")}}),
                migrations.CreateModel(name="ProjectPayment", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                    ("admin_commission", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                    ("employee_payout", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                    ("status", models.CharField(choices=[("pending","Pending"),("paid","Paid"),("failed","Failed")], default="pending", max_length=20)),
                    ("method", models.CharField(blank=True, max_length=50)),
                    ("transaction_id", models.CharField(blank=True, max_length=100)),
                    ("razorpay_order_id", models.CharField(blank=True, max_length=64)),
                    ("razorpay_payment_id", models.CharField(blank=True, max_length=64)),
                    ("razorpay_signature", models.CharField(blank=True, max_length=128)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_payments", to="pages.clientprofile")),
                    ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_payments", to="pages.employeeprofile")),
                    ("project", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment", to="pages.project")),
                ]),
                migrations.CreateModel(name="BankDetail", fields=[
                    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                    ("account_holder", models.CharField(max_length=160)),
                    ("account_number", models.CharField(max_length=30)),
                    ("ifsc_code", models.CharField(max_length=20)),
                    ("bank_name", models.CharField(max_length=120)),
                    ("branch_name", models.CharField(blank=True, max_length=160)),
                    ("account_type", models.CharField(choices=[("savings","Savings"),("current","Current")], default="savings", max_length=20)),
                    ("razorpay_contact_id", models.CharField(blank=True, max_length=64)),
                    ("razorpay_fund_account_id", models.CharField(blank=True, max_length=64)),
                    ("is_verified", models.BooleanField(default=False)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("updated_at", models.DateTimeField(auto_now=True)),
                    ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="bank_detail", to=settings.AUTH_USER_MODEL)),
                ], options={"ordering": ["-created_at"]}),
            ],
            # database_operations: only creates tables if they don't exist
            database_operations=[
                migrations.RunPython(create_tables_if_needed, migrations.RunPython.noop),
            ],
        ),
        # Seed data — uses get_or_create so safe on any database
        migrations.RunPython(seed_all, unseed_all),
    ]
