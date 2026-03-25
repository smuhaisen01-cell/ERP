from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='ChartOfAccount', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('code', models.CharField(max_length=10, unique=True)),
            ('name_ar', models.CharField(max_length=200)),
            ('name_en', models.CharField(max_length=200)),
            ('account_type', models.CharField(choices=[('asset','Asset'),('liability','Liability'),('equity','Equity'),('revenue','Revenue'),('expense','Expense')], max_length=15)),
            ('socpa_category', models.CharField(max_length=30, blank=True)),
            ('normal_balance', models.CharField(choices=[('debit','Debit'),('credit','Credit')], default='debit', max_length=10)),
            ('is_leaf', models.BooleanField(default=True)),
            ('is_active', models.BooleanField(default=True)),
            ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounting.chartofaccount')),
        ]),
        migrations.CreateModel(name='JournalEntry', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('entry_number', models.CharField(max_length=50, unique=True)),
            ('entry_date', models.DateField()),
            ('description_ar', models.TextField(blank=True)),
            ('description_en', models.TextField(blank=True)),
            ('reference', models.CharField(blank=True, max_length=100)),
            ('status', models.CharField(choices=[('draft','Draft'),('posted','Posted'),('reversed','Reversed')], default='draft', max_length=15)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('posted_at', models.DateTimeField(blank=True, null=True)),
            ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='journal_entries', to=settings.AUTH_USER_MODEL)),
            ('posted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posted_entries', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='JournalEntryLine', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('description_ar', models.CharField(blank=True, max_length=255)),
            ('debit_amount', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('credit_amount', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounting.chartofaccount')),
            ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='accounting.journalentry')),
        ]),
        migrations.CreateModel(name='VATReturn', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('period_start', models.DateField()),
            ('period_end', models.DateField()),
            ('status', models.CharField(default='draft', max_length=15)),
            ('total_sales', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('total_vat', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='ZakatReturn', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('fiscal_year', models.PositiveIntegerField()),
            ('status', models.CharField(default='draft', max_length=15)),
            ('zakatable_amount', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('zakat_due', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ]),
    ]
