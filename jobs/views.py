from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Job, Application, SavedJob, JobCategory
from .forms import JobPostForm, ApplicationForm, JobSearchForm
from accounts.models import UserProfile
from chat.models import Conversation, Message


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
