from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_remove_invoice_students_alter_invoice_status_and_more'),
        ('aggregator', '0005_universitydocvault_course'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoicelineitem',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='invoice_line_items', to='aggregator.course'),
        ),
        migrations.AlterField(
            model_name='invoicelineitem',
            name='course_fee',
            field=models.DecimalField(decimal_places=2, help_text='Locked total course fee at time of checkout', max_digits=12),
        ),
        migrations.AddField(
            model_name='invoicelineitem',
            name='gross_pool',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
        migrations.AddField(
            model_name='invoicelineitem',
            name='net_payable',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Amount charged to gateway for this line item', max_digits=12),
        ),
        migrations.AddField(
            model_name='invoicelineitem',
            name='rimit_commission',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
        migrations.AddField(
            model_name='invoicelineitem',
            name='sub_center_commission',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
        migrations.AddField(
            model_name='invoicelineitem',
            name='sub_center_commission_percent',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5),
        ),
        migrations.AddField(
            model_name='invoicelineitem',
            name='university_share',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
        migrations.AddField(
            model_name='invoicelineitem',
            name='university_share_percent',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5),
        ),
    ]
