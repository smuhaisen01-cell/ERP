"""Add PayrollRun, SaudizationReport, and missing Employee fields."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Missing Employee fields
        migrations.AddField(model_name='employee', name='passport_number',
            field=models.CharField(blank=True, max_length=30)),
        migrations.AddField(model_name='employee', name='other_allowances',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='بدلات أخرى')),
        migrations.AddField(model_name='employee', name='bank_name',
            field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='employee', name='iban',
            field=models.CharField(blank=True, max_length=34, verbose_name='رقم IBAN')),
        migrations.AddField(model_name='employee', name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='employee', name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True)),

        # PayrollRun model
        migrations.CreateModel(
            name='PayrollRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('period_month', models.PositiveSmallIntegerField()),
                ('period_year', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('draft','مسودة'),('approved','معتمد'),('processed','معالج'),('paid','مدفوع')], default='draft', max_length=15)),
                ('total_gross', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('total_gosi_employer', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('total_gosi_employee', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('total_net', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('wps_submitted', models.BooleanField(default=False)),
                ('wps_submitted_at', models.DateTimeField(blank=True, null=True)),
                ('wps_reference', models.CharField(blank=True, max_length=100)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payroll_runs', to=settings.AUTH_USER_MODEL)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'مسير الرواتب', 'unique_together': {('period_month', 'period_year')}},
        ),

        # SaudizationReport model
        migrations.CreateModel(
            name='SaudizationReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('report_date', models.DateField()),
                ('total_employees', models.PositiveIntegerField()),
                ('saudi_employees', models.PositiveIntegerField()),
                ('saudization_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('nitaqat_band', models.CharField(choices=[('platinum','بلاتيني'),('high_green','أخضر مرتفع'),('medium_green','أخضر متوسط'),('low_green','أخضر منخفض'),('yellow','أصفر'),('red','أحمر')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'تقرير السعودة'},
        ),
    ]
