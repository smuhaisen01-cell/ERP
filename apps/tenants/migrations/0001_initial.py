from django.db import migrations, models
import django_tenants.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('schema_name', models.CharField(db_index=True, max_length=63, serialize=False, primary_key=True)),
                # TenantMixin provides: created_on, paid_until, on_trial — do NOT re-declare
                ('name_ar', models.CharField(max_length=255, verbose_name='اسم الشركة (عربي)')),
                ('name_en', models.CharField(max_length=255, verbose_name='Company Name (English)')),
                ('vat_number', models.CharField(help_text='15-digit Saudi VAT registration number', max_length=15, unique=True, verbose_name='رقم تسجيل ضريبة القيمة المضافة')),
                ('cr_number', models.CharField(blank=True, help_text='Commercial Registration number', max_length=20, verbose_name='رقم السجل التجاري')),
                ('city', models.CharField(default='الرياض', max_length=100, verbose_name='المدينة')),
                ('address_ar', models.TextField(blank=True, verbose_name='العنوان (عربي)')),
                ('address_en', models.TextField(blank=True, verbose_name='Address (English)')),
                ('plan', models.CharField(choices=[('starter', 'Starter — 149 SAR/mo'), ('growth', 'Growth — 499 SAR/mo'), ('enterprise', 'Enterprise — Custom')], default='starter', max_length=20)),
                ('max_users', models.PositiveIntegerField(default=5)),
                ('max_invoices_per_month', models.PositiveIntegerField(default=300)),
                ('max_pos_terminals', models.PositiveIntegerField(default=1)),
                ('zatca_environment', models.CharField(choices=[('sandbox', 'Sandbox (Testing)'), ('simulation', 'Simulation'), ('production', 'Production')], default='sandbox', max_length=15)),
                ('zatca_onboarded', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'مستأجر',
                'verbose_name_plural': 'المستأجرون',
            },
            bases=(django_tenants.models.TenantMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(db_index=True, max_length=253, unique=True)),
                ('is_primary', models.BooleanField(default=True, db_index=True)),
                ('tenant', models.ForeignKey(on_delete=models.CASCADE, related_name='domains', to='tenants.tenant')),
            ],
            bases=(django_tenants.models.DomainMixin, models.Model),
        ),
    ]
