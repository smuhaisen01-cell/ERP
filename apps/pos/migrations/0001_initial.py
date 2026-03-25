from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('zatca', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(name='Branch', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('code', models.CharField(max_length=10, unique=True)),
            ('name_ar', models.CharField(max_length=100)),
            ('name_en', models.CharField(max_length=100)),
            ('city', models.CharField(default='Riyadh', max_length=50)),
            ('address_ar', models.TextField(blank=True)),
            ('is_active', models.BooleanField(default=True)),
        ]),
        migrations.CreateModel(name='POSTerminal', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('terminal_id', models.CharField(max_length=20, unique=True)),
            ('name', models.CharField(max_length=100)),
            ('is_active', models.BooleanField(default=True)),
            ('zatca_csid_registered', models.BooleanField(default=False)),
            ('zatca_registered_at', models.DateTimeField(blank=True, null=True)),
            ('branch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pos.branch')),
        ]),
        migrations.CreateModel(name='POSSession', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('opened_at', models.DateTimeField()),
            ('closed_at', models.DateTimeField(blank=True, null=True)),
            ('status', models.CharField(default='open', max_length=10)),
            ('opening_cash', models.DecimalField(decimal_places=2, max_digits=12)),
            ('closing_cash', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
            ('total_sales', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('total_vat', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('total_cash', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('total_mada', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('total_stc_pay', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('total_credit_card', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('transaction_count', models.PositiveIntegerField(default=0)),
            ('cashier', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ('terminal', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pos.posterminal')),
        ]),
        migrations.CreateModel(name='POSTransaction', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('transaction_number', models.CharField(max_length=50, unique=True)),
            ('payment_method', models.CharField(default='cash', max_length=20)),
            ('subtotal', models.DecimalField(decimal_places=2, max_digits=18)),
            ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('vat_amount', models.DecimalField(decimal_places=2, max_digits=18)),
            ('total_amount', models.DecimalField(decimal_places=2, max_digits=18)),
            ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('change_due', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('transacted_at', models.DateTimeField()),
            ('session', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='pos.possession')),
            ('zatca_invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='zatca.taxinvoice')),
        ]),
        migrations.CreateModel(name='POSTransactionLine', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('product_code', models.CharField(blank=True, max_length=50)),
            ('product_name_ar', models.CharField(max_length=200)),
            ('product_name_en', models.CharField(blank=True, max_length=200)),
            ('quantity', models.DecimalField(decimal_places=4, max_digits=12)),
            ('unit_price', models.DecimalField(decimal_places=4, max_digits=18)),
            ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('vat_rate', models.DecimalField(decimal_places=2, default=15, max_digits=5)),
            ('vat_amount', models.DecimalField(decimal_places=2, max_digits=18)),
            ('line_total', models.DecimalField(decimal_places=2, max_digits=18)),
            ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='pos.postransaction')),
        ]),
    ]
