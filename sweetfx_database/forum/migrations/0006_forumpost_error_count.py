# Generated manually (Django 2.2.6)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0005_auto_20250215_2247'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumpost',
            name='error_count',
            field=models.PositiveSmallIntegerField(default=0),
            preserve_default=False,
        ),
    ]
