from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('aggregator', '0003_course_search_vector_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='university',
            name='default_university_share_percent',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Default university share % of total fee (0-100). Used if course override is NULL.',
                max_digits=5,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
            ),
        ),
        migrations.AddField(
            model_name='course',
            name='university_share_percent',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Optional override: university share % of total fee (0-100). NULL = inherit from university.',
                max_digits=5,
                null=True,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
            ),
        ),
    ]
