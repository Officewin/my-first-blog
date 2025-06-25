from django.db import migrations, models, connection


def remove_level_field(apps, schema_editor):
    table = 'pronounce_dailypractice'
    column = 'level'
    with connection.cursor() as cursor:
        try:
            desc = connection.introspection.get_table_description(cursor, table)
        except Exception:
            return
        if column not in [col.name for col in desc]:
            return
    # use schema_editor to drop column for compatibility with old SQLite
    model = apps.get_model('pronounce', 'DailyPractice')
    field = models.CharField(max_length=20, default='beginner')
    field.set_attributes_from_name(column)
    schema_editor.remove_field(model, field)


class Migration(migrations.Migration):

    dependencies = [
        ('pronounce', '0004_remove_level_field'),
    ]

    operations = [
        migrations.RunPython(remove_level_field, migrations.RunPython.noop),
    ]
