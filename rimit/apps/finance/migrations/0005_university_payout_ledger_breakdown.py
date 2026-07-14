from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_invoice_lineitem_net_remittance'),
    ]

    operations = [
        migrations.AddField(
            model_name='universitypayoutledger',
            name='invoice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payout_ledgers', to='finance.invoice'),
        ),
        migrations.AddField(
            model_name='universitypayoutledger',
            name='transaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payout_ledgers', to='finance.transaction'),
        ),
        migrations.AddField(
            model_name='universitypayoutledger',
            name='total_fee',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
        migrations.AddField(
            model_name='universitypayoutledger',
            name='university_share',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
        migrations.AddField(
            model_name='universitypayoutledger',
            name='gross_pool',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
        migrations.AddField(
            model_name='universitypayoutledger',
            name='sub_center_commission',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
        migrations.AddField(
            model_name='universitypayoutledger',
            name='net_payable',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
    ]
