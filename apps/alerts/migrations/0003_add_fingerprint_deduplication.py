from django.db import migrations, models
import django.db.models.deletion
import hashlib


def backfill_fingerprints(apps, schema_editor):
    """Backfill fingerprints for existing RecruitmentEvents."""
    RecruitmentEvent = apps.get_model('alerts', 'RecruitmentEvent')
    
    for event in RecruitmentEvent.objects.all():
        # Generate a simple fingerprint from event_id (since we don't have title/deadline/positions yet)
        payload = f"event_id={event.event_id}"
        fingerprint = hashlib.sha256(payload.encode()).hexdigest()
        event.fingerprint = fingerprint
        event.status = 'NEW'
        event.save(update_fields=['fingerprint', 'status'])


def reverse_backfill(apps, schema_editor):
    """Reverse the backfill."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0002_recruitmentevent_decisionlog_alert_recruitment_event'),
    ]

    operations = [
        # Add fingerprint field (non-unique initially)
        migrations.AddField(
            model_name='recruitmentevent',
            name='fingerprint',
            field=models.CharField(
                max_length=64,
                help_text='SHA-256 fingerprint of recruitment identifying data. Used for deduplication.'
            ),
            preserve_default=False,
        ),
        # Add status field
        migrations.AddField(
            model_name='recruitmentevent',
            name='status',
            field=models.CharField(
                choices=[('NEW', 'New Recruitment Detected'), ('UPDATED', 'Existing Recruitment Updated'), ('CLOSED', 'Recruitment Closed')],
                db_index=True,
                default='NEW',
                max_length=20,
                help_text='Whether this is a new recruitment, an update, or closure.'
            ),
        ),
        # Add previous_event field
        migrations.AddField(
            model_name='recruitmentevent',
            name='previous_event',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='updates',
                to='alerts.recruitmentevent',
                help_text='If status=UPDATED, link to the previous event.'
            ),
        ),
        # Add title/deadline/positions to RecruitmentEvent
        migrations.AddField(
            model_name='recruitmentevent',
            name='title',
            field=models.CharField(
                blank=True,
                default='',
                max_length=500,
                help_text='Recruitment title for display and comparison.'
            ),
        ),
        migrations.AddField(
            model_name='recruitmentevent',
            name='deadline',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                help_text='Application deadline.'
            ),
        ),
        migrations.AddField(
            model_name='recruitmentevent',
            name='positions',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Positions available.'
            ),
        ),
        # Add fields to DecisionLog
        migrations.AddField(
            model_name='decisionlog',
            name='title',
            field=models.CharField(
                blank=True,
                default='',
                max_length=500,
                help_text='Recruitment title at time of decision.'
            ),
        ),
        migrations.AddField(
            model_name='decisionlog',
            name='deadline',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                help_text='Deadline at time of decision.'
            ),
        ),
        migrations.AddField(
            model_name='decisionlog',
            name='positions',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Positions at time of decision.'
            ),
        ),
        migrations.AddField(
            model_name='decisionlog',
            name='changes',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Fields that changed compared to previous event.'
            ),
        ),
        # Backfill fingerprints
        migrations.RunPython(backfill_fingerprints, reverse_backfill),
        # Now add unique constraint
        migrations.AlterField(
            model_name='recruitmentevent',
            name='fingerprint',
            field=models.CharField(
                max_length=64,
                unique=True,
                db_index=True,
                help_text='SHA-256 fingerprint of recruitment identifying data. Used for deduplication.'
            ),
        ),
    ]

