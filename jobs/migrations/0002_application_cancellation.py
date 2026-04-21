from django.db import migrations


def add_cancellation_columns(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(jobs_application)")
        cols = {row[1] for row in cursor.fetchall()}

        if 'cancellation_reason' not in cols:
            cursor.execute(
                "ALTER TABLE jobs_application ADD COLUMN cancellation_reason VARCHAR(100) NOT NULL DEFAULT ''"
            )
        if 'cancellation_detail' not in cols:
            cursor.execute(
                "ALTER TABLE jobs_application ADD COLUMN cancellation_detail TEXT NOT NULL DEFAULT ''"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_cancellation_columns, migrations.RunPython.noop),
    ]
