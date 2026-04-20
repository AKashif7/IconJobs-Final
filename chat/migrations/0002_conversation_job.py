from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='job',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional: link to specific job',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='conversations',
                to='jobs.job',
            ),
        ),
    ]
