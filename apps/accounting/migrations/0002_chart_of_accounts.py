"""Add ChartOfAccount model and fix JournalEntry/Line model names."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChartOfAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, max_length=20, verbose_name='رمز الحساب')),
                ('name_ar', models.CharField(max_length=255, verbose_name='اسم الحساب (عربي)')),
                ('name_en', models.CharField(max_length=255, verbose_name='Account Name (English)')),
                ('account_type', models.CharField(choices=[('asset','أصول'),('liability','خصوم'),('equity','حقوق ملكية'),('revenue','إيرادات'),('expense','مصروفات')], max_length=20)),
                ('socpa_category', models.CharField(choices=[('current_assets','الأصول المتداولة'),('non_current_assets','الأصول غير المتداولة'),('current_liabilities','الخصوم المتداولة'),('long_term_liabilities','الخصوم طويلة الأجل'),('equity','حقوق الملكية'),('revenue','الإيرادات'),('cogs','تكلفة المبيعات'),('operating_expenses','المصروفات التشغيلية'),('other_expenses','المصروفات الأخرى')], max_length=40)),
                ('is_active', models.BooleanField(default=True)),
                ('is_leaf', models.BooleanField(default=True)),
                ('normal_balance', models.CharField(choices=[('debit','Debit'),('credit','Credit')], max_length=6)),
                ('is_vat_account', models.BooleanField(default=False)),
                ('is_zakat_account', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='accounting.chartofaccount')),
            ],
            options={'verbose_name': 'دليل الحسابات'},
        ),
        # Rename JournalLine → JournalEntryLine to match model
        migrations.RenameModel(old_name='JournalLine', new_name='JournalEntryLine'),
        # Add missing updated_at to JournalEntry
        migrations.AddField(model_name='journalentry', name='updated_at',
            field=models.DateTimeField(auto_now=True)),
    ]
