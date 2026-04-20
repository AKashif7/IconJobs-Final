from django.db import migrations


def rebuild_message_table(apps, schema_editor):
    """
    Rebuild chat_message with the correct column names.
    The live DB was created from an older schema that may use 'timestamp'
    or 'created_at' instead of 'sent_at', and may be missing 'read_at'.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(chat_message)")
        cols = {row[1] for row in cursor.fetchall()}

        if 'sent_at' in cols and 'read_at' in cols:
            return  # Already correct schema, nothing to do

        # Determine which column holds the timestamp
        if 'sent_at' in cols:
            ts_col = 'sent_at'
        elif 'timestamp' in cols:
            ts_col = 'timestamp'
        elif 'created_at' in cols:
            ts_col = 'created_at'
        else:
            ts_col = None  # No timestamp column found

        # Build the SELECT for the copy — handle missing read_at
        if ts_col:
            select_ts = ts_col
        else:
            select_ts = "'2024-01-01 00:00:00'"

        if 'read_at' in cols:
            select_read = 'read_at'
        else:
            select_read = 'NULL'

        # Create replacement table
        cursor.execute("""
            CREATE TABLE chat_message_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                sent_at DATETIME NOT NULL DEFAULT '2024-01-01 00:00:00',
                read_at DATETIME NULL,
                conversation_id INTEGER NOT NULL REFERENCES chat_conversation(id) DEFERRABLE INITIALLY DEFERRED,
                sender_id INTEGER NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED
            )
        """)

        # Copy existing rows
        cursor.execute(f"""
            INSERT INTO chat_message_new (id, content, sent_at, read_at, conversation_id, sender_id)
            SELECT id, content, {select_ts}, {select_read}, conversation_id, sender_id
            FROM chat_message
        """)

        cursor.execute("DROP TABLE chat_message")
        cursor.execute("ALTER TABLE chat_message_new RENAME TO chat_message")


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_drop_application_column'),
    ]

    operations = [
        migrations.RunPython(rebuild_message_table, migrations.RunPython.noop),
    ]
