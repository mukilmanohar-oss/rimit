import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0002_subcenter_commission_percent'),
        ('aggregator', '0004_university_course_share_percents'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubCenterUniversityMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sub_center', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='university_mappings', to='partners.subcenter')),
                ('university', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_center_mappings', to='aggregator.university')),
            ],
            options={
                'db_table': 'sub_center_university_mappings',
                'unique_together': {('sub_center', 'university')},
            },
        ),
        migrations.AddIndex(
            model_name='subcenteruniversitymapping',
            index=models.Index(fields=['sub_center', 'university'], name='sub_center__sub_cen_68c6ab_idx'),
        ),
        migrations.AddIndex(
            model_name='subcenteruniversitymapping',
            index=models.Index(fields=['university'], name='sub_center__universi_5a6a27_idx'),
        ),
    ]
