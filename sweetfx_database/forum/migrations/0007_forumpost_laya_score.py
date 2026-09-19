from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0006_forumpost_error_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumpost',
            name='laya_score',
            field=models.FloatField(null=True),
        ),
    ]
