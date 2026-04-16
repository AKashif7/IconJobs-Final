"""
Run this script once to create:
- Admin superuser
- Sample employer account
- Sample job seeker account
- Sample job categories
- Sample job postings

Usage: python manage.py shell < setup_demo.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iconjobs_project.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from jobs.models import Job, JobCategory
from datetime import date, timedelta

print("Setting up IconJobs demo data...")

# --- CATEGORIES ---
cats = ['Office & Admin', 'Events & Hospitality', 'Retail & Sales', 'Warehouse & Logistics',
        'Cleaning & Maintenance', 'Data Entry & IT', 'Food & Catering', 'Customer Service']
created_cats = []
for name in cats:
    cat, _ = JobCategory.objects.get_or_create(name=name)
    created_cats.append(cat)
print(f"✓ {len(cats)} categories created")

# --- ADMIN ---
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@iconjobs.com', 'admin123')
    UserProfile.objects.create(user=admin, role='employer', company_name='IconJobs Admin')
    print("✓ Admin created  → username: admin  | password: admin123")

# --- EMPLOYER ---
if not User.objects.filter(username='employer1').exists():
    emp = User.objects.create_user('employer1', 'employer@demo.com', 'demo1234',
                                    first_name='Sarah', last_name='Thompson')
    UserProfile.objects.create(
        user=emp, role='employer',
        company_name='Thompson Events Ltd',
        company_description='London-based event management company running corporate and private events.',
        location='Soho, London',
        phone='07700900123',
        website='https://example.com',
        reveal_phone=True,
        reveal_email=True,
    )
    print("✓ Employer created → username: employer1 | password: demo1234")
else:
    emp = User.objects.get(username='employer1')

# --- JOB SEEKER ---
if not User.objects.filter(username='seeker1').exists():
    seek = User.objects.create_user('seeker1', 'seeker@demo.com', 'demo1234',
                                     first_name='James', last_name='Okafor')
    UserProfile.objects.create(
        user=seek, role='jobseeker',
        bio='Flexible and reliable student looking for short-term work in London.',
        location='Hackney, London',
        phone='07700900456',
        skills='Customer Service, Data Entry, Event Support, MS Office',
        availability='Weekdays and weekends',
        reveal_phone=True,
        reveal_email=True,
    )
    print("✓ Job Seeker created → username: seeker1 | password: demo1234")

# --- SAMPLE JOBS ---
today = date.today()
sample_jobs = [
    {
        'title': 'Event Staff – Corporate Conference',
        'description': 'We need reliable event staff for a corporate conference at a central London venue.\n\nDuties include:\n- Guest registration and check-in\n- Guiding attendees to sessions\n- Setting up and clearing tables\n- General front-of-house assistance\n\nSmart appearance required. No prior experience needed.',
        'location': 'Canary Wharf, London',
        'duration': '8h',
        'pay_rate': 12.50,
        'pay_type': 'hourly',
        'spots_available': 4,
        'start_date': today + timedelta(days=5),
        'cat': 'Events & Hospitality',
        'views': 24,
        'applications_count': 5,
    },
    {
        'title': 'Data Entry Clerk – Stock Database Update',
        'description': 'Small office task updating our product inventory spreadsheet.\n\nYou will:\n- Enter product codes and prices from printed sheets into Excel\n- Check for duplicate entries\n- Flag any discrepancies\n\nMust be comfortable with Excel and accurate typing.',
        'location': 'Shoreditch, London',
        'duration': '4h',
        'pay_rate': 11.00,
        'pay_type': 'hourly',
        'spots_available': 1,
        'start_date': today + timedelta(days=2),
        'cat': 'Data Entry & IT',
        'views': 15,
        'applications_count': 3,
    },
    {
        'title': 'Stockroom Assistant – Weekend Shift',
        'description': 'Busy retail store needs extra hands in the stockroom over the weekend.\n\nTasks:\n- Unpacking and organising deliveries\n- Labelling items\n- Moving stock to the shop floor\n\nMust be physically fit and able to lift boxes up to 15kg.',
        'location': 'Oxford Street, London',
        'duration': '2d',
        'pay_rate': 80.00,
        'pay_type': 'daily',
        'spots_available': 2,
        'start_date': today + timedelta(days=3),
        'cat': 'Warehouse & Logistics',
        'views': 31,
        'applications_count': 7,
    },
    {
        'title': 'Customer Service Rep – Pop-Up Stall',
        'description': 'We are running a promotional pop-up in a London shopping centre and need a friendly face.\n\nRole includes:\n- Engaging with shoppers\n- Explaining our product range\n- Processing sales on a tablet\n\nMust be outgoing and confident.',
        'location': 'Westfield Stratford, London',
        'duration': '5d',
        'pay_rate': 90.00,
        'pay_type': 'daily',
        'spots_available': 1,
        'start_date': today + timedelta(days=7),
        'cat': 'Customer Service',
        'views': 9,
        'applications_count': 2,
    },
    {
        'title': 'Office Cleaner – Early Morning Shift',
        'description': 'Small office in central London needs a cleaner for early morning shifts (6am–8am).\n\nTasks:\n- Vacuuming and mopping floors\n- Cleaning kitchen and bathrooms\n- Emptying bins and restocking supplies\n\nMust be punctual and reliable.',
        'location': 'Victoria, London',
        'duration': '2h',
        'pay_rate': 13.00,
        'pay_type': 'hourly',
        'spots_available': 1,
        'start_date': today + timedelta(days=1),
        'cat': 'Cleaning & Maintenance',
        'views': 6,
        'applications_count': 1,
    },
]

cat_map = {c.name: c for c in JobCategory.objects.all()}
for jdata in sample_jobs:
    if not Job.objects.filter(title=jdata['title'], employer=emp).exists():
        Job.objects.create(
            employer=emp,
            title=jdata['title'],
            description=jdata['description'],
            location=jdata['location'],
            duration=jdata['duration'],
            pay_rate=jdata['pay_rate'],
            pay_type=jdata['pay_type'],
            spots_available=jdata['spots_available'],
            start_date=jdata['start_date'],
            category=cat_map.get(jdata['cat']),
            views=jdata['views'],
            applications_count=jdata['applications_count'],
        )
print(f"✓ {len(sample_jobs)} sample jobs created")

print("\n========================================")
print("  IconJobs setup complete!")
print("========================================")
print("  Run: python manage.py runserver")
print("  Then open: http://127.0.0.1:8000")
print("")
print("  Admin Panel:  http://127.0.0.1:8000/admin/")
print("  Login:        admin / admin123")
print("")
print("  Demo Employer:   employer1 / demo1234")
print("  Demo Job Seeker: seeker1   / demo1234")
print("========================================")
