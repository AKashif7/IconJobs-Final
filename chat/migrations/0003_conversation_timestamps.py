from django.db import migrations, models


def add_timestamp_columns(apps, schema_editor):
    """Add created_at and last_message_at to chat_conversation if missing."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(chat_conversation)")
        existing = {row[1] for row in cursor.fetchall()}

        if 'created_at' not in existing:
            cursor.execute(
                "ALTER TABLE chat_conversation ADD COLUMN "
                "created_at datetime NOT NULL DEFAULT '2024-01-01 00:00:00'"
            )
        if 'last_message_at' not in existing:
            cursor.execute(
                "ALTER TABLE chat_conversation ADD COLUMN "
                "last_message_at datetime NOT NULL DEFAULT '2024-01-01 00:00:00'"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_conversation_job'),
    ]

    operations = [
        migrations.RunPython(add_timestamp_columns, migrations.RunPython.noop),
    ]
