from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm, ProfileEditForm, RatingForm
from .models import UserProfile, Rating
from jobs.models import Application


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to IconJobs, {user.first_name}!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(request.GET.get('next', 'home'))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_view(request, username=None):
    if username:
        target_user = get_object_or_404(User, username=username)
    else:
        target_user = request.user

    profile = get_object_or_404(UserProfile, user=target_user)

    # Check if viewer can see contact info (employer who accepted this seeker)
    can_see_contact = False
    if request.user != target_user and hasattr(request.user, 'profile'):
        if request.user.profile.role == 'employer':
            can_see_contact = Application.objects.filter(
                applicant=target_user,
                job__employer=request.user,
                status='accepted',
                contact_revealed=True
            ).exists()

    # Rating
    existing_rating = None
    if request.user != target_user:
        existing_rating = Rating.objects.filter(reviewer=request.user, reviewed=profile).first()

    can_rate = False
    if request.user != target_user and profile.role == 'jobseeker':
        # Employer who accepted and completed with this person can rate
        can_rate = Application.objects.filter(
            applicant=target_user,
            job__employer=request.user,
            status__in=['accepted', 'completed']
        ).exists()

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'target_user': target_user,
        'can_see_contact': can_see_contact,
        'existing_rating': existing_rating,
        'can_rate': can_rate,
    })


@login_required
def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile_obj = form.save(commit=False)
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            profile_obj.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form, 'profile': profile})


@login_required
def rate_user(request, username):
    target_user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=target_user)

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating, created = Rating.objects.update_or_create(
                reviewer=request.user,
                reviewed=profile,
                defaults={
                    'score': form.cleaned_data['score'],
                    'comment': form.cleaned_data['comment'],
                }
            )
            messages.success(request, 'Rating submitted!')
            return redirect('profile_username', username=username)
    return redirect('profile_username', username=username)
