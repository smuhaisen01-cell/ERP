import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_ar', models.CharField(max_length=200)),
                ('name_en', models.CharField(blank=True, max_length=200)),
                ('address_ar', models.TextField(blank=True)),
                ('city', models.CharField(default='الرياض', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'فرع',
            },
        ),
        migrations.CreateModel(
            name='POSTerminal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('terminal_id', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='terminals', to='pos.branch')),
            ],
            options={
                'verbose_name': 'طرفية نقطة البيع',
            },
        ),
        migrations.CreateModel(
            name='POSSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opened_at', models.DateTimeField(auto_now_add=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('opening_cash', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('closing_cash', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('closed', 'Closed')], default='open', max_length=10)),
                ('cashier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('terminal', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pos.posterminal')),
            ],
            options={
                'verbose_name': 'جلسة نقطة البيع',
            },
        ),
        migrations.CreateModel(
            name='POSTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_number', models.CharField(max_length=30, unique=True)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=12)),
                ('vat_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('mada', 'Mada'), ('visa', 'Visa'), ('mastercard', 'Mastercard'), ('stcpay', 'STC Pay'), ('applepay', 'Apple Pay')], max_length=15)),
                ('simplified_invoice_ref', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='pos.possession')),
            ],
            options={
                'verbose_name': 'معاملة نقطة البيع',
            },
        ),
    ]
