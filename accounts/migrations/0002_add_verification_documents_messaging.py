# migrations/0002_add_verification_documents_messaging.py
"""
Migration file to add:
- UserDocument model
- VerificationQueue model
- JobTitleSynonym model
- ApplicationDocument model
- Conversation and Message models for chat
- New fields to UserProfile
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),  # Adjust to match your latest migration
        ('jobs', '0001_initial'),      # Adjust to match your latest migration
    ]

    operations = [
        # ============ ACCOUNTS APP ============
        
        # Add verification fields to UserProfile
        migrations.AddField(
            model_name='userprofile',
            name='is_verified',
            field=models.BooleanField(default=False, help_text='Admin has verified this user'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='blue_tick_awarded',
            field=models.BooleanField(default=False, help_text='User has blue tick badge'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='verification_submitted_at',
            field=models.DateTimeField(null=True, blank=True, help_text='When user submitted documents'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='legal_name',
            field=models.CharField(blank=True, max_length=200, help_text="User's legal full name"),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone_for_otp',
            field=models.CharField(blank=True, max_length=20, help_text='Phone number for OTP verification'),
        ),
        
        # Create UserDocument model
        migrations.CreateModel(
            name='UserDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(
                    choices=[
                        ('profile_photo', 'Profile Photo'),
                        ('dbs_check', 'DBS Check Certificate'),
                        ('national_insurance', 'National Insurance Document'),
                        ('work_permit_visa', 'Work Permit / Visa')
                    ],
                    max_length=30
                )),
                ('file', models.FileField(upload_to='user_documents/%Y/%m/%d/')),
                ('file_name', models.CharField(max_length=255)),
                ('file_size_bytes', models.IntegerField()),
                ('is_verified', models.BooleanField(default=False)),
                ('admin_notes', models.TextField(blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='auth.user')),
            ],
            options={
                'ordering': ['-uploaded_at'],
                'unique_together': {('user', 'document_type')},
            },
        ),
        
        # Create VerificationQueue model
        migrations.CreateModel(
            name='VerificationQueue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                    default='pending',
                    max_length=20
                )),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('admin_notes', models.TextField(blank=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verifications_reviewed', to='auth.user')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='verification_queue', to='auth.user')),
            ],
            options={
                'ordering': ['submitted_at'],
            },
        ),
        
        # ============ JOBS APP ============
        
        # Create JobTitleSynonym model
        migrations.CreateModel(
            name='JobTitleSynonym',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primary_title', models.CharField(max_length=100)),
                ('synonym', models.CharField(max_length=100)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Job Title Synonyms',
                'ordering': ['primary_title'],
                'unique_together': {('primary_title', 'synonym')},
            },
        ),
        
        # Create ApplicationDocument model
        migrations.CreateModel(
            name='ApplicationDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='applications/%Y/%m/%d/')),
                ('file_name', models.CharField(max_length=255)),
                ('file_size_bytes', models.IntegerField()),
                ('is_from_profile', models.BooleanField(default=False, help_text='True if using existing CV from profile')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('document_order', models.IntegerField(default=0, help_text='Order of documents in application')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='jobs.application')),
            ],
            options={
                'ordering': ['document_order', 'uploaded_at'],
            },
        ),
        
        # ============ CHAT APP ============
        
        # Create Conversation model
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_message_at', models.DateTimeField(auto_now=True)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conversations', to='jobs.job')),
                ('participants', models.ManyToManyField(related_name='conversations', to='auth.user')),
            ],
            options={
                'ordering': ['-last_message_at'],
            },
        ),
        
        # Create Message model
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True, help_text='When message was read by recipient')),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.conversation')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='auth.user')),
            ],
            options={
                'ordering': ['sent_at'],
            },
        ),
        
        # Create TypingIndicator model
        migrations.CreateModel(
            name='TypingIndicator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='typing_indicators', to='chat.conversation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
            options={
                'unique_together': {('conversation', 'user')},
            },
        ),
    ]
