from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subcenter',
            name='commission_percent',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Sub-center commission % of gross pool (0-100). Deducted upfront at checkout.',
                max_digits=5,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
            ),
        ),
    ]
