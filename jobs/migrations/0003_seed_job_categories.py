from django.db import migrations


DEFAULT_CATEGORIES = [
    ('Hospitality',          'cup-hot'),
    ('Retail',               'bag'),
    ('Warehouse & Logistics','box-seam'),
    ('Events & Promotions',  'calendar-event'),
    ('Cleaning & Facilities','stars'),
    ('Food & Beverage',      'egg-fried'),
    ('Security',             'shield-check'),
    ('Administration',       'file-earmark-text'),
    ('Delivery & Driving',   'truck'),
    ('Construction & Trades','hammer'),
    ('Healthcare & Care',    'heart-pulse'),
    ('Technology & IT',      'laptop'),
    ('Other',                'briefcase'),
]


def seed_categories(apps, schema_editor):
    JobCategory = apps.get_model('jobs', 'JobCategory')
    for name, icon in DEFAULT_CATEGORIES:
        JobCategory.objects.get_or_create(name=name, defaults={'icon': icon})


def unseed_categories(apps, schema_editor):
    JobCategory = apps.get_model('jobs', 'JobCategory')
    names = [name for name, _ in DEFAULT_CATEGORIES]
    JobCategory.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_application_cancellation'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_code=unseed_categories),
    ]
