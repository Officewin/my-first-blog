from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('pronounce', '0003_add_dailysubmission'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailypractice',
            name='level',
            field=models.CharField(default='beginner', max_length=20),
        ),
    ]
