import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantZATCACredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant_schema', models.CharField(db_index=True, max_length=100)),
                ('terminal_id', models.CharField(blank=True, max_length=50)),
                ('credential_type', models.CharField(choices=[('tenant', 'Tenant (ERP)'), ('terminal', 'POS Terminal')], max_length=10)),
                ('private_key_encrypted', models.BinaryField()),
                ('binary_security_token', models.TextField()),
                ('secret', models.CharField(max_length=255)),
                ('environment', models.CharField(choices=[('sandbox', 'Sandbox'), ('simulation', 'Simulation'), ('production', 'Production')], max_length=15)),
                ('issued_at', models.DateTimeField()),
                ('expires_at', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('renewed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'شهادة ZATCA',
                'unique_together': {('tenant_schema', 'terminal_id', 'environment')},
            },
        ),
        migrations.CreateModel(
            name='ZATCAInvoiceLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant_schema', models.CharField(db_index=True, max_length=100)),
                ('invoice_uuid', models.UUIDField(db_index=True)),
                ('invoice_number', models.CharField(max_length=50)),
                ('invoice_type', models.CharField(max_length=10)),
                ('invoice_hash', models.CharField(max_length=64)),
                ('previous_hash', models.CharField(max_length=64)),
                ('zatca_status', models.CharField(max_length=20)),
                ('zatca_response', models.JSONField(default=dict)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('cleared_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'سجل فاتورة ZATCA',
            },
        ),
        migrations.CreateModel(
            name='TaxInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('invoice_number', models.CharField(max_length=50, unique=True)),
                ('invoice_type', models.CharField(choices=[('388', 'Tax Invoice (B2B)'), ('386', 'Simplified Invoice (B2C)'), ('381', 'Credit Note'), ('383', 'Debit Note')], max_length=10)),
                ('issue_date', models.DateField()),
                ('issue_time', models.TimeField()),
                ('hijri_date', models.CharField(blank=True, max_length=20)),
                ('supply_date', models.DateField(blank=True, null=True)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=16)),
                ('discount_total', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('taxable_amount', models.DecimalField(decimal_places=2, max_digits=16)),
                ('vat_amount', models.DecimalField(decimal_places=2, max_digits=16)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=16)),
                ('currency', models.CharField(default='SAR', max_length=3)),
                ('buyer_name', models.CharField(blank=True, max_length=255)),
                ('buyer_vat', models.CharField(blank=True, max_length=15)),
                ('buyer_cr', models.CharField(blank=True, max_length=20)),
                ('signed_xml', models.TextField(blank=True)),
                ('qr_tlv', models.TextField(blank=True)),
                ('invoice_hash', models.CharField(blank=True, max_length=64)),
                ('previous_hash', models.CharField(blank=True, max_length=64)),
                ('zatca_status', models.CharField(choices=[('draft', 'Draft'), ('signed', 'Signed'), ('pending_clearance', 'Pending Clearance'), ('cleared', 'Cleared'), ('pending_reporting', 'Pending Reporting'), ('reported', 'Reported'), ('rejected', 'Rejected')], default='draft', max_length=25)),
                ('zatca_response', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'فاتورة ضريبية',
                'ordering': ['-issue_date', '-invoice_number'],
            },
        ),
    ]
