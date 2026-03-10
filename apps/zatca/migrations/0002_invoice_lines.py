"""Add TaxInvoiceLine model."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zatca', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxInvoiceLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('line_number', models.PositiveSmallIntegerField()),
                ('description_ar', models.CharField(max_length=500)),
                ('description_en', models.CharField(blank=True, max_length=500)),
                ('quantity', models.DecimalField(decimal_places=4, max_digits=12)),
                ('unit', models.CharField(default='EA', max_length=20)),
                ('unit_price', models.DecimalField(decimal_places=4, max_digits=18)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ('line_total', models.DecimalField(decimal_places=2, max_digits=18)),
                ('vat_rate', models.DecimalField(decimal_places=2, default=15, max_digits=5)),
                ('vat_amount', models.DecimalField(decimal_places=2, max_digits=18)),
                ('vat_category_code', models.CharField(default='S', max_length=5)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='zatca.taxinvoice')),
            ],
            options={'ordering': ['line_number']},
        ),
    ]
