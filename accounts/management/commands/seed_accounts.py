"""
Django management command: python manage.py seed_accounts seed_data.csv

Creates job seeker and employer accounts from CSV file with their associated data.
"""

import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from accounts.models import UserProfile
from jobs.models import Job, JobCategory
from pathlib import Path


class Command(BaseCommand):
    help = 'Seed accounts (job seekers and employers) from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file with account data')

    @transaction.atomic
    def handle(self, *args, **options):
        csv_file = options['csv_file']

        # Check file exists
        if not Path(csv_file).exists():
            raise CommandError(f'File not found: {csv_file}')

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            jobseeker_count = 0
            employer_count = 0
            job_count = 0

            for row_num, row in enumerate(reader, start=2):
                try:
                    email = row.get('email', '').strip()
                    password = row.get('password', '').strip()
                    legal_name = row.get('legal_name', '').strip()
                    phone_number = row.get('phone_number', '').strip()
                    user_type = row.get('user_type', '').strip()
                    company_name = row.get('company_name', '').strip()

                    # Validation
                    if not all([email, password, user_type]):
                        self.stdout.write(
                            self.style.WARNING(f'Row {row_num}: Missing required fields, skipping')
                        )
                        continue

                    if user_type not in ['job_seeker', 'employer']:
                        self.stdout.write(
                            self.style.WARNING(f'Row {row_num}: Invalid user_type "{user_type}", skipping')
                        )
                        continue

                    # Create user
                    username = email.split('@')[0]  # Use first part of email as username
                    try:
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                            first_name=legal_name.split()[0] if legal_name else username,
                            last_name=' '.join(legal_name.split()[1:]) if legal_name and len(legal_name.split()) > 1 else ''
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'Row {row_num}: Could not create user - {str(e)}')
                        )
                        continue

                    # Create profile
                    profile = UserProfile.objects.create(
                        user=user,
                        role=user_type,
                        legal_name=legal_name,
                        phone_for_otp=phone_number,
                        is_verified=True,  # Auto-verify seeded accounts
                        blue_tick_awarded=True  # Auto-award blue tick
                    )

                    if user_type == 'job_seeker':
                        jobseeker_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Job seeker created: {email}')
                        )

                    elif user_type == 'employer':
                        # Create employer profile
                        if company_name:
                            profile.company_name = company_name
                            profile.save(update_fields=['company_name'])

                        # Create 3 jobs for this employer
                        job_titles = [
                            row.get('job_title_1', '').strip(),
                            row.get('job_title_2', '').strip(),
                            row.get('job_title_3', '').strip(),
                        ]
                        job_titles = [t for t in job_titles if t]  # Filter empty

                        for idx, job_title in enumerate(job_titles, start=1):
                            try:
                                job = Job.objects.create(
                                    employer=user,
                                    title=job_title,
                                    description=f'{job_title} position at {company_name or user.username}',
                                    location='UK Wide',
                                    duration='2w',
                                    pay_rate=20 + (idx * 5),
                                    pay_type='hourly',
                                    spots_available=1,
                                    status='open',
                                    start_date='2025-04-28'
                                )
                                job_count += 1
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(f'  Could not create job "{job_title}": {str(e)}')
                                )

                        employer_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Employer created: {email} ({company_name}) with {len(job_titles)} jobs')
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Row {row_num}: Unexpected error - {str(e)}')
                    )
                    continue

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🎉 SEEDING COMPLETE!'))
        self.stdout.write('='*50)
        self.stdout.write(f'📊 Statistics:')
        self.stdout.write(f'   • Job seekers created: {jobseeker_count}')
        self.stdout.write(f'   • Employers created: {employer_count}')
        self.stdout.write(f'   • Jobs created: {job_count}')
        self.stdout.write(f'   • Total listings: {job_count}')
        self.stdout.write('')
