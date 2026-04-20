from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm, ProfileEditForm, RatingForm, DocumentUploadForm
from jobs.models import Application
from django.db.models import Q
import json
from .models import UserProfile, UserDocument, VerificationQueue, Rating
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse


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
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Try to find user by email first, then by username
        user = None
        if '@' in username_or_email:
            # It's an email
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        # If not found by email or no @ sign, try username
        if user is None:
            user = authenticate(request, username=username_or_email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(request.GET.get('next', 'home'))
        else:
            messages.error(request, 'Invalid email/username or password.')
    
    return render(request, 'accounts/login.html', {})


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

    # Documents visible to own user, or to an employer who accepted them
    show_documents = (request.user == target_user) or can_see_contact
    doc_items = []
    if show_documents and profile.role == 'jobseeker':
        docs_dict = {d.document_type: d for d in UserDocument.objects.filter(user=target_user)}
        for dtype, label in [
            ('dbs_check', 'DBS Check'),
            ('national_insurance', 'National Insurance'),
            ('work_permit_visa', 'Work Permit / Visa'),
        ]:
            doc_items.append({'label': label, 'dtype': dtype, 'doc': docs_dict.get(dtype)})

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'target_user': target_user,
        'can_see_contact': can_see_contact,
        'existing_rating': existing_rating,
        'can_rate': can_rate,
        'doc_items': doc_items,
        'show_documents': show_documents,
    })


@login_required
def edit_profile(request):
    from django.contrib.auth import update_session_auth_hash
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        password_error = None

        # Handle password change if any password field is filled
        current_pw = request.POST.get('current_password', '').strip()
        new_pw1 = request.POST.get('new_password1', '').strip()
        new_pw2 = request.POST.get('new_password2', '').strip()
        changing_password = any([current_pw, new_pw1, new_pw2])

        if changing_password:
            if not current_pw:
                password_error = 'Please enter your current password.'
            elif not request.user.check_password(current_pw):
                password_error = 'Current password is incorrect.'
            elif not new_pw1:
                password_error = 'Please enter a new password.'
            elif len(new_pw1) < 8:
                password_error = 'New password must be at least 8 characters.'
            elif new_pw1 != new_pw2:
                password_error = 'New passwords do not match.'

        if form.is_valid() and not password_error:
            profile_obj = form.save(commit=False)
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            profile_obj.save()

            if changing_password:
                request.user.set_password(new_pw1)
                request.user.save()
                update_session_auth_hash(request, request.user)

            # Save verification documents (job seekers only)
            if profile.role == 'jobseeker':
                for doc_type in ['dbs_check', 'national_insurance', 'work_permit_visa']:
                    file_obj = request.FILES.get(doc_type)
                    if file_obj:
                        UserDocument.objects.update_or_create(
                            user=request.user,
                            document_type=doc_type,
                            defaults={
                                'file': file_obj,
                                'file_name': file_obj.name,
                                'file_size_bytes': file_obj.size,
                                'is_verified': False,
                            }
                        )

            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        elif password_error:
            messages.error(request, password_error)
    else:
        form = ProfileEditForm(instance=profile)

    uploaded_docs = {doc.document_type: doc for doc in UserDocument.objects.filter(user=request.user)}
    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'profile': profile,
        'uploaded_docs': uploaded_docs,
    })


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


# ============ FEATURE 1 & 2: Document Upload & Verification ============

@login_required
@require_http_methods(["GET", "POST"])
def upload_documents_view(request):
    """
    Allow job seekers to upload documents (profile photo, DBS, NIN, work permit)
    Handles both initial registration and profile updates
    """
    profile = get_object_or_404(UserProfile, user=request.user)
    
    # Only job seekers can upload documents
    if profile.role != 'jobseeker':
        messages.error(request, 'Only job seekers can upload documents.')
        return redirect('edit_profile')

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get form data
                legal_name = form.cleaned_data.get('legal_name')
                phone_for_otp = form.cleaned_data.get('phone_for_otp')
                
                # Update profile with legal name and phone
                profile.legal_name = legal_name
                profile.phone_for_otp = phone_for_otp
                profile.save()

                # Process each document type
                document_types = [
                    'profile_photo',
                    'dbs_check',
                    'national_insurance',
                    'work_permit_visa'
                ]

                uploaded_count = 0
                for doc_type in document_types:
                    file_obj = request.FILES.get(doc_type)
                    if file_obj:
                        # Create or update document
                        doc, created = UserDocument.objects.update_or_create(
                            user=request.user,
                            document_type=doc_type,
                            defaults={
                                'file': file_obj,
                                'file_name': file_obj.name,
                                'file_size_bytes': file_obj.size
                            }
                        )
                        uploaded_count += 1

                # Create or update verification queue entry
                verification, created = VerificationQueue.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'status': 'pending',
                    }
                )

                messages.success(
                    request,
                    f'✅ {uploaded_count} document(s) uploaded! Our admin team will review within 24 hours.'
                )
                return redirect('profile')

            except Exception as e:
                messages.error(request, f'Upload failed: {str(e)}')
                return redirect('upload_documents')
    else:
        form = DocumentUploadForm()

    # Get already uploaded documents
    uploaded_docs = UserDocument.objects.filter(user=request.user)
    verification_status = VerificationQueue.objects.filter(user=request.user).first()

    context = {
        'form': form,
        'uploaded_docs': {doc.document_type: doc for doc in uploaded_docs},
        'verification_status': verification_status,
        'profile': profile
    }
    return render(request, 'accounts/upload_documents.html', context)


@login_required
@require_http_methods(["GET"])
def get_user_documents_api(request, user_id):
    """
    API endpoint to fetch uploaded documents for a user
    Used by admin dashboard and application forms
    """
    try:
        user = get_object_or_404(User, id=user_id)
        documents = UserDocument.objects.filter(user=user)
        
        doc_data = {}
        for doc in documents:
            doc_data[doc.document_type] = {
                'id': doc.id,
                'file_url': doc.file.url if doc.file else None,
                'file_name': doc.file_name,
                'file_size_bytes': doc.file_size_bytes,
                'uploaded_at': doc.uploaded_at.isoformat(),
                'is_verified': doc.is_verified,
            }
        
        return JsonResponse(doc_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ============ ADMIN VERIFICATION DASHBOARD ============

def is_admin(user):
    """Check if user is admin"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def admin_verification_dashboard(request):
    """
    Admin dashboard to review and approve/reject user documents
    Awards blue tick badge upon approval
    """
    
    # Get pending verifications
    pending = VerificationQueue.objects.filter(status='pending').select_related('user')
    approved = VerificationQueue.objects.filter(status='approved').select_related('user')
    rejected = VerificationQueue.objects.filter(status='rejected').select_related('user')

    context = {
        'pending_count': pending.count(),
        'approved_count': approved.count(),
        'rejected_count': rejected.count(),
        'pending': pending[:10],  # Show latest 10
        'tab': request.GET.get('tab', 'pending')
    }

    if context['tab'] == 'approved':
        context['verifications'] = approved[:10]
    elif context['tab'] == 'rejected':
        context['verifications'] = rejected[:10]
    else:
        context['verifications'] = pending

    return render(request, 'accounts/admin_verification_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def admin_review_user(request, user_id):
    """
    Detailed review page for a specific user
    Shows all documents and verification status
    """
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    documents = UserDocument.objects.filter(user=user)
    verification = VerificationQueue.objects.filter(user=user).first()

    context = {
        'target_user': user,
        'profile': profile,
        'documents': {doc.document_type: doc for doc in documents},
        'verification': verification,
    }
    return render(request, 'accounts/admin_review_detail.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_approve_user(request, user_id):
    """
    AJAX endpoint: Approve user and award blue tick
    """
    try:
        user = get_object_or_404(User, id=user_id)
        profile = get_object_or_404(UserProfile, user=user)
        verification = VerificationQueue.objects.get(user=user)

        # Award blue tick
        profile.is_verified = True
        profile.blue_tick_awarded = True
        profile.save()

        # Update verification queue
        verification.status = 'approved'
        verification.reviewed_by = request.user
        verification.admin_notes = request.POST.get('admin_notes', '')
        verification.save()

        # TODO: Send email to user notifying approval
        # send_verification_email(user, 'approved')

        return JsonResponse({
            'success': True,
            'message': f'✅ {user.username} approved and blue tick awarded!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def admin_reject_user(request, user_id):
    """
    AJAX endpoint: Reject user (requires rejection reason)
    """
    try:
        user = get_object_or_404(User, id=user_id)
        verification = VerificationQueue.objects.get(user=user)
        
        rejection_reason = request.POST.get('rejection_reason', '')
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'error': 'Please provide a rejection reason'
            }, status=400)

        # Update verification queue
        verification.status = 'rejected'
        verification.reviewed_by = request.user
        verification.rejection_reason = rejection_reason
        verification.admin_notes = request.POST.get('admin_notes', '')
        verification.save()

        # TODO: Send email to user notifying rejection
        # send_verification_email(user, 'rejected', rejection_reason)

        return JsonResponse({
            'success': True,
            'message': f'User {user.username} rejected.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def verification_status_api(request):
    """
    AJAX: Get current user's verification status
    Used to show badge status on profile
    """
    profile = get_object_or_404(UserProfile, user=request.user)
    verification = VerificationQueue.objects.filter(user=request.user).first()

    data = {
        'is_verified': profile.is_verified,
        'blue_tick_awarded': profile.blue_tick_awarded,
        'verification_status': verification.status if verification else None,
        'rejection_reason': verification.rejection_reason if verification and verification.status == 'rejected' else None,
    }
    return JsonResponse(data)
