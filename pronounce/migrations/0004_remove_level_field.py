from django.db import migrations, connection


def remove_level_field(apps, schema_editor):
    table = 'pronounce_dailypractice'
    column = 'level'
    with connection.cursor() as cursor:
        try:
            desc = connection.introspection.get_table_description(cursor, table)
        except Exception:
            return
        columns = [col.name for col in desc]
        if column in columns:
            schema_editor.execute(f'ALTER TABLE {table} DROP COLUMN {column}')


class Migration(migrations.Migration):

    dependencies = [
        ('pronounce', '0003_add_dailysubmission'),
    ]

    operations = [
        migrations.RunPython(remove_level_field, migrations.RunPython.noop),
    ]

