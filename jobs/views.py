from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Job, Application, SavedJob, JobCategory
from .forms import JobPostForm, ApplicationForm, JobSearchForm
from chat.models import Conversation, Message
from django.views.decorators.http import require_http_methods
from .models import Job, JobTitleSynonym
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json
from jobs.models import Application, ApplicationDocument
from accounts.models import UserProfile, UserDocument
from django.utils import timezone

# All view functions for the jobs app. This is the largest view file in the
# project — it covers the homepage, job listings, applying, employer
# management, dashboards, the smart search API, and the extended application
# flow with CV uploads.


# ── Static/informational pages ────────────────────────────────────────────

def career_guide(request):
    # Just renders the static career advice page — no data needed.
    return render(request, 'jobs/career_guide.html')


def about(request):
    return render(request, 'jobs/about.html')


def contact(request):
    # On a POST (form submission), flip the submitted flag so the template
    # can show a thank-you message. Also pass the user's role so the template
    # can personalise the message if they're logged in.
    submitted = False
    if request.method == 'POST':
        submitted = True
    role = None
    if request.user.is_authenticated:
        try:
            role = request.user.profile.role
        except Exception:
            pass
    return render(request, 'jobs/contact.html', {'submitted': submitted, 'role': role})


# ── Homepage ──────────────────────────────────────────────────────────────

def home(request):
    # Pulls up to 6 trending jobs (sorted by application count then views)
    # and up to 6 recently posted jobs for the two sections on the homepage.
    # Also counts all open jobs for the "X open positions" display.
    trending_jobs = Job.objects.filter(status='open').order_by('-applications_count', '-views')[:6]
    recent_jobs = Job.objects.filter(status='open').order_by('-created_at')[:6]
    categories = JobCategory.objects.all()
    total_jobs = Job.objects.filter(status='open').count()
    return render(request, 'jobs/home.html', {
        'trending_jobs': trending_jobs,
        'recent_jobs': recent_jobs,
        'categories': categories,
        'total_jobs': total_jobs,
    })


# ── Job listings & detail ─────────────────────────────────────────────────

def job_list(request):
    # Starts with all open jobs and narrows them down based on whatever
    # filters the user submitted via the search form (keyword, location,
    # duration, category). Uses Django's Q objects for OR queries.
    form = JobSearchForm(request.GET)
    jobs = Job.objects.filter(status='open')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        location = form.cleaned_data.get('location')
        duration = form.cleaned_data.get('duration')
        category = form.cleaned_data.get('category')

        if q:
            jobs = jobs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if location:
            jobs = jobs.filter(location__icontains=location)
        if duration:
            jobs = jobs.filter(duration=duration)
        if category:
            jobs = jobs.filter(category=category)

    return render(request, 'jobs/job_list.html', {'jobs': jobs, 'form': form})


def job_detail(request, pk):
    # Increments the view counter each time someone opens a job page —
    # this feeds into the trending algorithm without a separate analytics tool.
    job = get_object_or_404(Job, pk=pk)
    job.views += 1
    job.save(update_fields=['views'])

    already_applied = False
    is_saved = False
    application = None

    # Check application/save status for logged-in users so the template
    # can show the right button state (Apply / Applied / Save / Saved).
    if request.user.is_authenticated:
        application = Application.objects.filter(job=job, applicant=request.user).first()
        already_applied = application is not None
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'already_applied': already_applied,
        'is_saved': is_saved,
        'application': application,
    })


# ── Applying for jobs ─────────────────────────────────────────────────────

@login_required
def apply_job(request, pk):
    # Standard application flow. Several guard checks run before the form
    # is even shown: the user must be a job seeker, can't apply to their own
    # listing, and can't apply to the same job twice.
    job = get_object_or_404(Job, pk=pk)
    profile = get_object_or_404(UserProfile, user=request.user)

    if profile.role != 'jobseeker':
        messages.error(request, 'Only job seekers can apply for jobs.')
        return redirect('job_detail', pk=pk)

    if job.employer == request.user:
        messages.error(request, 'You cannot apply to your own job.')
        return redirect('job_detail', pk=pk)

    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, 'You have already applied to this job.')
        return redirect('job_detail', pk=pk)

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()

            # Increment the counter on the job so trending stays accurate.
            job.applications_count += 1
            job.save(update_fields=['applications_count'])

            # Process any files the user uploaded alongside their application.
            for i, f in enumerate(request.FILES.getlist('documents')):
                if f.size > 0:
                    ApplicationDocument.objects.create(
                        application=application,
                        file=f,
                        file_name=f.name,
                        file_size_bytes=f.size,
                        document_order=i,
                    )
            messages.success(request, 'Application submitted! The employer will review your profile.')
            return redirect('job_detail', pk=pk)
    else:
        form = ApplicationForm()

    return render(request, 'jobs/apply.html', {'form': form, 'job': job})


# ── Saved jobs ────────────────────────────────────────────────────────────

@login_required
def save_job(request, pk):
    # Toggle save state. If the SavedJob record doesn't exist yet, create it
    # (saved). If it does, delete it (unsaved). Returns JSON so the frontend
    # can update the button without reloading the page.
    job = get_object_or_404(Job, pk=pk)
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        saved.delete()
        return JsonResponse({'saved': False})
    return JsonResponse({'saved': True})


@login_required
def saved_jobs(request):
    saves = SavedJob.objects.filter(user=request.user).select_related('job')
    return render(request, 'jobs/saved_jobs.html', {'saves': saves})


# ── Posting and editing jobs (employer only) ──────────────────────────────

@login_required
def post_job(request):
    # Only employers can reach this page — job seekers are bounced back home.
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.role != 'employer':
        messages.error(request, 'Only employers can post jobs.')
        return redirect('home')

    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            # Assign the logged-in employer as the owner of this listing.
            job.employer = request.user
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('employer_dashboard')
    else:
        form = JobPostForm()

    return render(request, 'jobs/post_job.html', {'form': form})


@login_required
def edit_job(request, pk):
    # get_object_or_404 with employer=request.user ensures employers can
    # only edit their own listings — trying to edit someone else's job
    # returns a 404 rather than an error message.
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    if request.method == 'POST':
        form = JobPostForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated!')
            return redirect('employer_dashboard')
    else:
        form = JobPostForm(instance=job)
    return render(request, 'jobs/post_job.html', {'form': form, 'editing': True, 'job': job})


@login_required
def close_job(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    job.status = 'closed'
    job.save()
    messages.success(request, f'"{job.title}" has been closed.')
    return redirect('employer_dashboard')


# ── Dashboards ────────────────────────────────────────────────────────────

@login_required
def employer_dashboard(request):
    # Redirects non-employers away. Lists all jobs posted by this employer,
    # newest first, so they can quickly see what's active or needs attention.
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.role != 'employer':
        return redirect('home')

    jobs = Job.objects.filter(employer=request.user).order_by('-created_at')
    return render(request, 'jobs/employer_dashboard.html', {'jobs': jobs})


@login_required
def view_applicants(request, job_pk):
    # Shows all applications for a specific job. select_related and
    # prefetch_related reduce the number of database queries when the
    # template iterates through applicants and their documents.
    job = get_object_or_404(Job, pk=job_pk, employer=request.user)
    applications = job.applications.select_related('applicant__profile').prefetch_related('documents').order_by('-applied_at')
    return render(request, 'jobs/applicants.html', {'job': job, 'applications': applications})


@login_required
def update_application(request, app_pk):
    # Handles the employer's accept/reject/shortlist/complete actions on an
    # applicant. Accepting automatically opens a chat conversation and sends
    # an introductory message so communication can start immediately.
    application = get_object_or_404(Application, pk=app_pk, job__employer=request.user)
    action = request.POST.get('action')

    if action == 'accept':
        application.status = 'accepted'
        application.contact_revealed = True
        application.save()

        # Find an existing conversation for this job+applicant pair, or
        # create a new one if this is the first acceptance.
        qs = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=application.applicant
        ).filter(
            job=application.job
        )
        if qs.exists():
            conv = qs.first()
            created = False
        else:
            conv = Conversation.objects.create(job=application.job)
            conv.participants.add(request.user, application.applicant)
            created = True

        # Only send the auto-message when the conversation is brand new —
        # don't spam it if the employer re-accepts after reversing a decision.
        if created:
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                content=f"Hi {application.applicant.first_name or application.applicant.username}, great news — you have been accepted for '{application.job.title}'! Let's coordinate the details.",
            )
        messages.success(request, f'{application.applicant.get_full_name() or application.applicant.username} has been accepted! A chat has been opened.')

    elif action == 'reject':
        application.status = 'rejected'
        application.save()
        messages.info(request, 'Applicant rejected.')

    elif action == 'shortlist':
        application.status = 'shortlisted'
        application.save()
        messages.success(request, 'Applicant shortlisted.')

    elif action == 'complete':
        application.status = 'completed'
        application.save()
        messages.success(request, 'Job marked as completed.')

    return redirect('view_applicants', job_pk=application.job.pk)


@login_required
def cancel_application(request, app_pk):
    # Lets an employer cancel an application they've already accepted or
    # shortlisted — with a mandatory reason so the seeker understands why.
    application = get_object_or_404(Application, pk=app_pk, job__employer=request.user)

    if application.status not in ('accepted', 'shortlisted', 'pending'):
        messages.error(request, 'This application cannot be cancelled.')
        return redirect('view_applicants', job_pk=application.job.pk)

    # Predefined reasons keep the data consistent and avoid free-text abuse.
    CANCEL_REASONS = [
        ('position_filled', 'Position has been filled by someone else'),
        ('job_cancelled', 'The job has been cancelled'),
        ('schedule_conflict', 'Schedule or timing no longer works'),
        ('budget_change', 'Budget constraints or pay rate changed'),
        ('applicant_unresponsive', 'Applicant has not responded'),
        ('role_changed', 'Role requirements have changed significantly'),
        ('business_closed', 'Business is temporarily or permanently closed'),
        ('other', 'Other reason'),
    ]

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        detail = request.POST.get('detail', '').strip()
        if not reason:
            return render(request, 'jobs/cancel_application.html', {
                'application': application,
                'job': application.job,
                'reasons': CANCEL_REASONS,
                'error': 'Please select a reason.',
            })
        application.status = 'cancelled'
        application.cancellation_reason = reason
        application.cancellation_detail = detail
        application.save()
        messages.success(request, f'Application for {application.applicant.get_full_name() or application.applicant.username} has been cancelled.')
        return redirect('view_applicants', job_pk=application.job.pk)

    return render(request, 'jobs/cancel_application.html', {
        'application': application,
        'job': application.job,
        'reasons': CANCEL_REASONS,
    })


@login_required
def jobseeker_dashboard(request):
    # Shows the job seeker all their submitted applications, newest first.
    # Non-seekers are bounced to the homepage.
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.role != 'jobseeker':
        return redirect('home')

    applications = Application.objects.filter(applicant=request.user).select_related('job').order_by('-applied_at')
    return render(request, 'jobs/jobseeker_dashboard.html', {'applications': applications})


# ── Smart search API ──────────────────────────────────────────────────────

@require_http_methods(["GET"])
def search_jobs(request):
    # Intelligent job search that expands the query using the synonym table.
    # Searching "cashier" also returns jobs titled "till worker" or
    # "checkout assistant" without the seeker needing to try each term.
    query = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()

    if len(query) < 2:
        return JsonResponse({
            'success': False,
            'error': 'Search query too short (minimum 2 characters)',
            'results': []
        })

    try:
        # Step 1: Look up synonyms for the search term in both directions
        # (query could match either the primary_title or the synonym column).
        synonyms_qs = JobTitleSynonym.objects.filter(
            Q(primary_title__icontains=query) | Q(synonym__icontains=query)
        )

        # Collect every related title into a set to deduplicate.
        matching_titles = set()
        for syn in synonyms_qs:
            matching_titles.add(syn.primary_title.lower())
            matching_titles.add(syn.synonym.lower())

        # Always include the original search term even if it has no synonyms.
        matching_titles.add(query.lower())

        # Step 2: Search across all matching titles.
        jobs_query = Job.objects.filter(
            Q(title__icontains=query) |
            Q(title__icontains__in=list(matching_titles))
        )

        if location:
            jobs_query = jobs_query.filter(location__icontains=location)

        jobs_query = jobs_query.filter(status='open').order_by('-created_at')

        results = []
        for job in jobs_query[:50]:
            results.append({
                'id': job.id,
                'title': job.title,
                'company': job.employer.first_name or job.employer.username,
                'location': job.location,
                'duration': job.get_duration_display(),
                'pay_rate': str(job.pay_rate),
                'pay_type': job.get_pay_type_display(),
                'url': f'/jobs/{job.id}/'
            })

        return JsonResponse({
            'success': True,
            'search_query': query,
            'matched_titles': list(matching_titles),
            'total_results': len(results),
            'location_filter': location if location else None,
            'results': results
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'results': []
        }, status=500)


@require_http_methods(["GET"])
def get_job_title_suggestions(request):
    # Powers the autocomplete dropdown as someone types in the search bar.
    # Pulls matching job titles from the database and related synonyms,
    # deduplicates them, and returns up to 15 suggestions.
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'suggestions': []})

    try:
        titles = Job.objects.filter(
            title__icontains=query
        ).values_list('title', flat=True).distinct()[:10]

        synonyms = JobTitleSynonym.objects.filter(
            Q(primary_title__icontains=query) | Q(synonym__icontains=query)
        ).values_list('primary_title', flat=True).distinct()[:5]

        all_suggestions = list(set(list(titles) + list(synonyms)))

        return JsonResponse({
            'suggestions': all_suggestions[:15]
        })
    except Exception as e:
        return JsonResponse({'suggestions': []})

        from django.shortcuts import render, redirect, get_object_or_40


# ── Extended application flow (with CV uploads) ───────────────────────────

@login_required
@require_http_methods(["GET", "POST"])
def apply_for_job(request, job_id):
    # Alternative, more detailed application route that supports uploading
    # files alongside the cover message. Seekers can either use their
    # profile CV or upload fresh documents (up to 5 files, max 10MB each).
    job = get_object_or_404(Job, id=job_id)
    profile = get_object_or_404(UserProfile, user=request.user)

    existing_application = Application.objects.filter(job=job, applicant=request.user).first()
    if existing_application:
        messages.warning(request, 'You have already applied for this job.')
        return redirect('job_detail', job_id=job_id)

    if profile.role != 'jobseeker':
        messages.error(request, 'Only job seekers can apply for jobs.')
        return redirect('job_detail', job_id=job_id)

    if request.method == 'GET':
        # Pull the seeker's profile CV (if they have one) so the template
        # can offer to re-use it instead of uploading a new copy.
        profile_cv = UserDocument.objects.filter(
            user=request.user,
            document_type='profile_photo'
        ).first()

        context = {
            'job': job,
            'profile': profile,
            'profile_cv': profile_cv,
        }
        return render(request, 'jobs/apply_for_job.html', context)

    elif request.method == 'POST':
        try:
            cover_message = request.POST.get('cover_message', '').strip()
            cv_option = request.POST.get('cv_option')  # 'profile' or 'upload'

            application = Application.objects.create(
                job=job,
                applicant=request.user,
                cover_message=cover_message,
                status='pending'
            )

            # If the seeker chose to reuse their profile CV, copy it across
            # to the application documents with the is_from_profile flag set.
            if cv_option == 'profile':
                profile_cv = UserDocument.objects.filter(
                    user=request.user,
                    document_type='cv'
                ).first()

                if profile_cv:
                    ApplicationDocument.objects.create(
                        application=application,
                        file=profile_cv.file,
                        file_name=profile_cv.file_name,
                        file_size_bytes=profile_cv.file_size_bytes,
                        is_from_profile=True,
                        document_order=0
                    )

            # Process any files uploaded for this application specifically.
            uploaded_files = request.FILES.getlist('documents')
            if len(uploaded_files) > 5:
                application.delete()
                messages.error(request, 'Maximum 5 files per application.')
                return redirect('apply_for_job', job_id=job_id)

            for idx, file_obj in enumerate(uploaded_files):
                if file_obj.size > 10 * 1024 * 1024:
                    # Roll back the application if any file is too large
                    # so we don't leave orphaned records.
                    application.delete()
                    messages.error(request, f'{file_obj.name} is too large (max 10MB).')
                    return redirect('apply_for_job', job_id=job_id)

                ApplicationDocument.objects.create(
                    application=application,
                    file=file_obj,
                    file_name=file_obj.name,
                    file_size_bytes=file_obj.size,
                    is_from_profile=False,
                    document_order=idx + 1
                )

            # Recalculate and sync the denormalised application count on the job.
            job.applications_count = job.applications.count()
            job.save(update_fields=['applications_count'])

            messages.success(request, '✅ Application submitted successfully!')
            return redirect('job_detail', job_id=job_id)

        except Exception as e:
            messages.error(request, f'Application failed: {str(e)}')
            return redirect('apply_for_job', job_id=job_id)


@login_required
@require_http_methods(["GET"])
def my_applications(request):
    # Shows the logged-in seeker a list of all applications they've submitted,
    # with extra context (days since applied, document count, status label)
    # so they can track progress at a glance.
    applications = Application.objects.filter(applicant=request.user).select_related('job').prefetch_related('documents')

    app_data = []
    for app in applications:
        app_data.append({
            'application': app,
            'job': app.job,
            'status_display': app.get_status_display(),
            'document_count': app.documents.count(),
            'days_ago': (timezone.now() - app.applied_at).days
        })

    context = {'applications': app_data}
    return render(request, 'jobs/my_applications.html', context)


@login_required
@require_http_methods(["GET"])
def application_detail(request, application_id):
    # Shows the full details of a single application including all attached
    # documents. Accessible to both the applicant and the job's employer —
    # anyone else gets bounced to the homepage.
    application = get_object_or_404(Application, id=application_id)

    if request.user != application.applicant and request.user != application.job.employer:
        messages.error(request, 'You don\'t have permission to view this application.')
        return redirect('home')

    documents = application.documents.all()

    context = {
        'application': application,
        'job': application.job,
        'documents': documents,
        'applicant': application.applicant,
    }
    return render(request, 'jobs/application_detail.html', context)


@login_required
@require_http_methods(["GET"])
def job_applications_for_employer(request):
    # Gives employers a combined view of all applications across all their
    # job listings, grouped by job so it's easy to compare candidates.
    profile = get_object_or_404(UserProfile, user=request.user)

    if profile.role != 'employer':
        messages.error(request, 'Only employers can view applications.')
        return redirect('home')

    applications = Application.objects.filter(
        job__employer=request.user
    ).select_related('job', 'applicant').prefetch_related('documents')

    # Group the flat queryset into a dict keyed by job ID.
    jobs_with_apps = {}
    for app in applications:
        if app.job.id not in jobs_with_apps:
            jobs_with_apps[app.job.id] = {
                'job': app.job,
                'applications': []
            }
        jobs_with_apps[app.job.id]['applications'].append(app)

    context = {
        'jobs_with_apps': jobs_with_apps.values(),
        'total_applications': len(applications)
    }
    return render(request, 'jobs/employer_applications.html', context)


# ── Application management JSON APIs ─────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def update_application_status(request, application_id):
    # AJAX endpoint for the employer panel to change an application's status
    # without a full page reload. Validates the new status against the model's
    # STATUS_CHOICES before saving.
    try:
        application = get_object_or_404(Application, id=application_id)

        if request.user != application.job.employer:
            return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

        new_status = request.POST.get('status')
        if new_status not in dict(Application.STATUS_CHOICES):
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

        application.status = new_status
        application.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f'Application status updated to {application.get_status_display()}',
            'new_status': application.get_status_display()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def get_application_documents(request, application_id):
    # Returns the list of documents for an application as JSON. Used by
    # the employer's applicant review panel to load documents dynamically.
    # Only the applicant or the job's employer can call this.
    try:
        application = get_object_or_404(Application, id=application_id)

        if request.user != application.applicant and request.user != application.job.employer:
            return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

        documents = application.documents.all()

        doc_data = []
        for doc in documents:
            doc_data.append({
                'id': doc.id,
                'file_name': doc.file_name,
                'file_size_bytes': doc.file_size_bytes,
                'file_url': doc.file.url if doc.file else None,
                'is_from_profile': doc.is_from_profile,
                'uploaded_at': doc.uploaded_at.isoformat(),
            })

        return JsonResponse({
            'success': True,
            'documents': doc_data,
            'total': len(doc_data)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
