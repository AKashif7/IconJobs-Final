from django.db import migrations


def drop_application_column(apps, schema_editor):
    """Remove legacy application_id column if it exists on chat_conversation."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(chat_conversation)")
        existing = {row[1] for row in cursor.fetchall()}
        if 'application_id' in existing:
            cursor.execute("ALTER TABLE chat_conversation DROP COLUMN application_id")


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_conversation_timestamps'),
    ]

    operations = [
        migrations.RunPython(drop_application_column, migrations.RunPython.noop),
    ]
