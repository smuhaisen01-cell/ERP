"""
Add fields that exist in the Tenant model but were missing from 0001_initial.
The DB already has the table from 0001 — this adds the missing columns.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        # trial_ends_at was in the model but missing from 0001
        migrations.AddField(
            model_name='tenant',
            name='trial_ends_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
