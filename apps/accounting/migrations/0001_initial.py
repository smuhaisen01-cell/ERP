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
            name='AccountCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True)),
                ('name_ar', models.CharField(max_length=100)),
                ('name_en', models.CharField(max_length=100)),
                ('normal_balance', models.CharField(choices=[('debit', 'Debit'), ('credit', 'Credit')], max_length=6)),
            ],
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, max_length=20, unique=True)),
                ('name_ar', models.CharField(max_length=255)),
                ('name_en', models.CharField(blank=True, max_length=255)),
                ('account_type', models.CharField(choices=[('asset', 'Asset'), ('liability', 'Liability'), ('equity', 'Equity'), ('revenue', 'Revenue'), ('expense', 'Expense')], max_length=15)),
                ('normal_balance', models.CharField(choices=[('debit', 'Debit'), ('credit', 'Credit')], max_length=6)),
                ('is_active', models.BooleanField(default=True)),
                ('allow_direct_posting', models.BooleanField(default=True)),
                ('vat_account', models.BooleanField(default=False)),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='accounting.account')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounting.accountcategory')),
            ],
            options={
                'verbose_name': 'حساب',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='JournalEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_number', models.CharField(max_length=20, unique=True)),
                ('entry_date', models.DateField()),
                ('description_ar', models.TextField()),
                ('description_en', models.TextField(blank=True)),
                ('reference', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('posted', 'Posted'), ('voided', 'Voided')], default='draft', max_length=10)),
                ('total_debit', models.DecimalField(decimal_places=2, max_digits=18)),
                ('total_credit', models.DecimalField(decimal_places=2, max_digits=18)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'قيد محاسبي',
                'ordering': ['-entry_date', '-entry_number'],
            },
        ),
        migrations.CreateModel(
            name='JournalLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('debit', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('credit', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounting.account')),
                ('journal_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='accounting.journalentry')),
            ],
        ),
        migrations.CreateModel(
            name='VATReturn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('box_1_standard_rated_sales', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('box_2_vat_on_sales', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('box_6_standard_rated_purchases', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('box_7_vat_on_purchases', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('box_9_net_vat_due', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('filed', 'Filed'), ('paid', 'Paid')], default='draft', max_length=10)),
                ('filed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'إقرار ضريبة القيمة المضافة',
            },
        ),
        migrations.CreateModel(
            name='ZakatReturn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fiscal_year', models.PositiveIntegerField()),
                ('zakatable_assets', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('zakatable_liabilities', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('zakat_base', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('zakat_due', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('filed', 'Filed'), ('paid', 'Paid')], default='draft', max_length=10)),
            ],
            options={
                'verbose_name': 'إقرار الزكاة',
            },
        ),
    ]
