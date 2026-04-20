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


def career_guide(request):
    return render(request, 'jobs/career_guide.html')


def about(request):
    return render(request, 'jobs/about.html')


def contact(request):
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


def home(request):
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


def job_list(request):
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
    job = get_object_or_404(Job, pk=pk)
    job.views += 1
    job.save(update_fields=['views'])

    already_applied = False
    is_saved = False
    application = None

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


@login_required
def apply_job(request, pk):
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
            job.applications_count += 1
            job.save(update_fields=['applications_count'])
            messages.success(request, 'Application submitted! The employer will review your profile.')
            return redirect('job_detail', pk=pk)
    else:
        form = ApplicationForm()

    return render(request, 'jobs/apply.html', {'form': form, 'job': job})


@login_required
def save_job(request, pk):
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


@login_required
def post_job(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.role != 'employer':
        messages.error(request, 'Only employers can post jobs.')
        return redirect('home')

    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('employer_dashboard')
    else:
        form = JobPostForm()

    return render(request, 'jobs/post_job.html', {'form': form})


@login_required
def edit_job(request, pk):
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


@login_required
def employer_dashboard(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.role != 'employer':
        return redirect('home')

    jobs = Job.objects.filter(employer=request.user).order_by('-created_at')
    return render(request, 'jobs/employer_dashboard.html', {'jobs': jobs})


@login_required
def view_applicants(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, employer=request.user)
    applications = job.applications.select_related('applicant__profile').order_by('-applied_at')
    return render(request, 'jobs/applicants.html', {'job': job, 'applications': applications})


@login_required
def update_application(request, app_pk):
    """Employer accepts, rejects, shortlists, or marks complete"""
    application = get_object_or_404(Application, pk=app_pk, job__employer=request.user)
    action = request.POST.get('action')

    if action == 'accept':
        application.status = 'accepted'
        application.contact_revealed = True
        application.save()
        # Create a conversation automatically
        conv, created = Conversation.objects.get_or_create(application=application)
        if created:
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                content=f"Hi {application.applicant.first_name or application.applicant.username}, great news — you have been accepted for '{application.job.title}'! Let's coordinate the details.",
                is_system=False
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
def jobseeker_dashboard(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.role != 'jobseeker':
        return redirect('home')

    applications = Application.objects.filter(applicant=request.user).select_related('job').order_by('-applied_at')
    return render(request, 'jobs/jobseeker_dashboard.html', {'applications': applications})



@require_http_methods(["GET"])
def search_jobs(request):
    """
    Intelligent job search with synonym matching
    Example: Search "cashier" returns "cashier", "till worker", "checkout assistant", etc.
    """
    query = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()
    
    if len(query) < 2:
        return JsonResponse({
            'success': False,
            'error': 'Search query too short (minimum 2 characters)',
            'results': []
        })

    try:
        # Step 1: Find all synonyms for the search query
        synonyms_qs = JobTitleSynonym.objects.filter(
            Q(primary_title__icontains=query) | Q(synonym__icontains=query)
        )

        # Collect all matching titles (primary + synonyms)
        matching_titles = set()
        for syn in synonyms_qs:
            matching_titles.add(syn.primary_title.lower())
            matching_titles.add(syn.synonym.lower())

        # Always add the original query
        matching_titles.add(query.lower())

        # Step 2: Search jobs with all matching titles
        jobs_query = Job.objects.filter(
            Q(title__icontains=query) |
            Q(title__icontains__in=list(matching_titles))
        )

        # Filter by location if provided
        if location:
            jobs_query = jobs_query.filter(location__icontains=location)

        # Only show open jobs
        jobs_query = jobs_query.filter(status='open')

        # Order by most recent
        jobs_query = jobs_query.order_by('-created_at')

        # Prepare response
        results = []
        for job in jobs_query[:50]:  # Limit to 50 results
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
    """
    AJAX endpoint: Get job title suggestions as user types
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'suggestions': []})

    try:
        # Get unique job titles from database
        titles = Job.objects.filter(
            title__icontains=query
        ).values_list('title', flat=True).distinct()[:10]

        # Also get synonyms
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


@login_required
@require_http_methods(["GET", "POST"])
def apply_for_job(request, job_id):
    """
    Job application form with flexible CV upload options
    User can:
    - Option A: Use existing CV from profile
    - Option B: Upload new CV(s) for this specific application
    - Up to 5 files per application
    """
    job = get_object_or_404(Job, id=job_id)
    profile = get_object_or_404(UserProfile, user=request.user)

    # Check if already applied
    existing_application = Application.objects.filter(job=job, applicant=request.user).first()
    if existing_application:
        messages.warning(request, 'You have already applied for this job.')
        return redirect('job_detail', job_id=job_id)

    # Only job seekers can apply
    if profile.role != 'jobseeker':
        messages.error(request, 'Only job seekers can apply for jobs.')
        return redirect('job_detail', job_id=job_id)

    if request.method == 'GET':
        # Show application form
        profile_cv = UserDocument.objects.filter(
            user=request.user,
            document_type='profile_photo'  # Or use CV if you have a separate field
        ).first()

        context = {
            'job': job,
            'profile': profile,
            'profile_cv': profile_cv,
        }
        return render(request, 'jobs/apply_for_job.html', context)

    elif request.method == 'POST':
        # Process application
        try:
            cover_message = request.POST.get('cover_message', '').strip()
            cv_option = request.POST.get('cv_option')  # 'profile' or 'upload'

            # Create application
            application = Application.objects.create(
                job=job,
                applicant=request.user,
                cover_message=cover_message,
                status='pending'
            )

            # Step 1: Add CV from profile if selected
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

            # Step 2: Add uploaded documents
            uploaded_files = request.FILES.getlist('documents')
            if len(uploaded_files) > 5:
                application.delete()
                messages.error(request, 'Maximum 5 files per application.')
                return redirect('apply_for_job', job_id=job_id)

            for idx, file_obj in enumerate(uploaded_files):
                # Validate file size (10MB max)
                if file_obj.size > 10 * 1024 * 1024:
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

            # Update job applications count
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
    """
    Show all applications submitted by current user
    """
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
    """
    View details of a specific application
    """
    application = get_object_or_404(Application, id=application_id)

    # Check: User is applicant OR employer of the job
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
    """
    View all applications for jobs posted by current user (employer)
    """
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if profile.role != 'employer':
        messages.error(request, 'Only employers can view applications.')
        return redirect('home')

    # Get applications for all jobs posted by this employer
    applications = Application.objects.filter(
        job__employer=request.user
    ).select_related('job', 'applicant').prefetch_related('documents')

    # Group by job
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


@login_required
@require_http_methods(["POST"])
def update_application_status(request, application_id):
    """
    AJAX endpoint: Change application status (pending → shortlisted → accepted, etc.)
    """
    try:
        application = get_object_or_404(Application, id=application_id)
        
        # Check: User is employer
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
    """
    AJAX endpoint: Get all documents for an application
    """
    try:
        application = get_object_or_404(Application, id=application_id)
        
        # Check access
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


