from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aggregator', '0004_university_course_share_percents'),
    ]

    operations = [
        migrations.AddField(
            model_name='universitydocvault',
            name='course',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional course mapping for course-specific prospectus/library tiles.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='documents',
                to='aggregator.course',
            ),
        ),
        migrations.AddIndex(
            model_name='universitydocvault',
            index=models.Index(fields=['course', 'doc_type'], name='university_d_course_i_0d9f50_idx'),
        ),
    ]
