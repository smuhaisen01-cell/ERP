import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_ar', models.CharField(max_length=100, verbose_name='اسم القسم (عربي)')),
                ('name_en', models.CharField(max_length=100, verbose_name='Department Name (English)')),
                ('cost_center', models.CharField(blank=True, max_length=20)),
            ],
            options={
                'verbose_name': 'قسم',
            },
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_number', models.CharField(max_length=20, unique=True)),
                ('first_name_ar', models.CharField(max_length=100)),
                ('last_name_ar', models.CharField(max_length=100)),
                ('first_name_en', models.CharField(blank=True, max_length=100)),
                ('last_name_en', models.CharField(blank=True, max_length=100)),
                ('national_id', models.CharField(max_length=20, unique=True)),
                ('iqama_number', models.CharField(blank=True, max_length=20)),
                ('nationality', models.CharField(choices=[('saudi', 'Saudi'), ('expat', 'Expatriate')], max_length=10)),
                ('job_title_ar', models.CharField(max_length=200)),
                ('job_title_en', models.CharField(blank=True, max_length=200)),
                ('hire_date', models.DateField(verbose_name='تاريخ التعيين')),
                ('termination_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('terminated', 'Terminated'), ('on_leave', 'On Leave')], default='active', max_length=15)),
                ('basic_salary', models.DecimalField(decimal_places=2, max_digits=12)),
                ('housing_allowance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('transport_allowance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('gosi_number', models.CharField(blank=True, max_length=30)),
                ('bank_iban', models.CharField(blank=True, max_length=34)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hr.department')),
            ],
            options={
                'verbose_name': 'موظف',
            },
        ),
        migrations.AddField(
            model_name='department',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_departments', to='hr.employee'),
        ),
    ]
