from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_tenants.models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Tenant', fields=[
            ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
            ('schema_name', models.CharField(db_index=True, max_length=63, unique=True, validators=[django_tenants.models._check_schema_name])),
            ('name_ar', models.CharField(max_length=255)),
            ('name_en', models.CharField(max_length=255)),
            ('vat_number', models.CharField(max_length=15, unique=True)),
            ('cr_number', models.CharField(blank=True, max_length=20)),
            ('city', models.CharField(default='الرياض', max_length=100)),
            ('address_ar', models.TextField(blank=True)),
            ('address_en', models.TextField(blank=True)),
            ('plan', models.CharField(default='starter', max_length=20)),
            ('max_users', models.PositiveIntegerField(default=5)),
            ('max_invoices_per_month', models.PositiveIntegerField(default=300)),
            ('max_pos_terminals', models.PositiveIntegerField(default=1)),
            ('zatca_environment', models.CharField(default='sandbox', max_length=15)),
            ('zatca_onboarded', models.BooleanField(default=False)),
            ('is_active', models.BooleanField(default=True)),
            ('trial_ends_at', models.DateTimeField(blank=True, null=True)),
            ('auto_create_schema', models.BooleanField(default=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ]),
        migrations.CreateModel(name='Domain', fields=[
            ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
            ('domain', models.CharField(db_index=True, max_length=253, unique=True)),
            ('is_primary', models.BooleanField(db_index=True, default=True)),
            ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='domains', to='tenants.tenant')),
        ]),
        migrations.CreateModel(name='UserProfile', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('role', models.CharField(default='employee', max_length=20)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='erp_profile', to=settings.AUTH_USER_MODEL)),
        ]),
    ]
