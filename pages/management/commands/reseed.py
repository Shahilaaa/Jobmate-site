"""
Management command: python manage.py reseed
Wipes ALL data and re-seeds from scratch using the migration's seed function.
Use this when migrating to a new system with an existing database.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Wipe all data and reseed the database from scratch'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('⚠️  Wiping ALL data and reseeding...'))

        # Import and run the seed function directly
        from pages.squashed_seed import run_seed
        run_seed()

        self.stdout.write(self.style.SUCCESS('✅ Database reseeded successfully!'))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('  Admin:    admin@jobmate.com      / Admin@1234')
        self.stdout.write('  Employee: arjun.nair@jobmate.com / Employee@1234')
        self.stdout.write('  Client:   eva.pillai@jobmate.com / Client@1234')
