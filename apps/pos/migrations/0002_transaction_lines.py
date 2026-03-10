"""Add POSTransactionLine model."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='POSTransactionLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('product_code', models.CharField(max_length=50)),
                ('product_name_ar', models.CharField(max_length=255)),
                ('product_name_en', models.CharField(blank=True, max_length=255)),
                ('quantity', models.DecimalField(decimal_places=4, max_digits=12)),
                ('unit_price', models.DecimalField(decimal_places=4, max_digits=12)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('vat_rate', models.DecimalField(decimal_places=2, default=15, max_digits=5)),
                ('vat_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('line_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='pos.postransaction')),
            ],
        ),
    ]
