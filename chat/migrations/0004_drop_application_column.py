from django.db import migrations


def rebuild_conversation_table(apps, schema_editor):
    """
    Recreate chat_conversation without the legacy application_id column.
    SQLite cannot DROP a column that has a UNIQUE constraint, so we must
    rebuild the table from scratch.
    """
    with schema_editor.connection.cursor() as cursor:
        # Check current columns
        cursor.execute("PRAGMA table_info(chat_conversation)")
        cols = {row[1] for row in cursor.fetchall()}

        if 'application_id' not in cols:
            return  # Already clean, nothing to do

        # Create replacement table with the correct schema
        cursor.execute("""
            CREATE TABLE chat_conversation_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME NOT NULL DEFAULT '2024-01-01 00:00:00',
                last_message_at DATETIME NOT NULL DEFAULT '2024-01-01 00:00:00',
                job_id INTEGER NULL REFERENCES jobs_job(id) DEFERRABLE INITIALLY DEFERRED
            )
        """)

        # Copy existing rows (exclude application_id)
        cursor.execute("""
            INSERT INTO chat_conversation_new (id, created_at, last_message_at, job_id)
            SELECT id, created_at, last_message_at, job_id
            FROM chat_conversation
        """)

        # Drop old table and rename new one
        cursor.execute("DROP TABLE chat_conversation")
        cursor.execute("ALTER TABLE chat_conversation_new RENAME TO chat_conversation")


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_conversation_timestamps'),
    ]

    operations = [
        migrations.RunPython(rebuild_conversation_table, migrations.RunPython.noop),
    ]
