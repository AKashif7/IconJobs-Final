from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, Rating, UserDocument, VerificationQueue

# All form classes for the accounts app. These define the fields, widgets,
# validation rules, and save logic for registration, login, profile editing,
# document uploads, and user ratings. Django forms handle both the HTML
# rendering and server-side validation, which keeps things DRY.


class RegisterForm(UserCreationForm):
    # Extends Django's built-in UserCreationForm to add the extra fields
    # IconJobs needs: email, first/last name, role selection, and the two
    # agreement checkboxes required by the platform's terms.

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'your@email.com'
        })
    )
    first_name = forms.CharField(
        max_length=50, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=50, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Last name'
        })
    )

    # The role field determines whether the user becomes a job seeker or
    # an employer. This drives almost everything else on the platform.
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )

    # Both checkboxes are mandatory — users must actively agree before
    # they can create an account.
    agree_terms = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'Please accept the Terms & Conditions to create an account.'
        }
    )
    agree_authentic = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'You must confirm that your profile information is 100% authentic.'
        }
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to the fields that come from the parent
        # class (username, password1, password2) — the ones defined above
        # already have their attrs set inline.
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirm your password'
        })

    def save(self, commit=True):
        # Save the User first (via the parent), then also copy the extra
        # fields across and create the linked UserProfile with the chosen role.
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(user=user, role=self.cleaned_data['role'])
        return user


class LoginForm(AuthenticationForm):
    # Thin wrapper around Django's AuthenticationForm — just applies
    # Bootstrap classes so the login page matches the rest of the site.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Your username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Your password'
        })


class ProfileEditForm(forms.ModelForm):
    # Lets users update their UserProfile and their underlying Django User
    # record (first name, last name, email) in a single form. The __init__
    # method strips out fields that don't apply to the user's role so
    # employers don't see seeker-only fields and vice versa.

    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'})
    )

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'phone', 'profile_picture', 'cv',
            'skills', 'availability', 'company_name', 'company_description',
            'website', 'reveal_phone', 'reveal_email'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4, 'class': 'form-control',
                'placeholder': 'Tell employers a little about yourself, your experience and what you bring to the table...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. Shoreditch, London'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '+44 7xxx xxxxxx'
            }),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'cv': forms.FileInput(attrs={'class': 'form-control'}),
            'skills': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Python, Communication, Teamwork (comma separated)'
            }),
            'availability': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Weekdays, evenings, weekends'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Your company or trading name'
            }),
            'company_description': forms.Textarea(attrs={
                'rows': 4, 'class': 'form-control',
                'placeholder': 'Describe what your company does and what makes it a great place to work...'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control', 'placeholder': 'https://yourcompany.com'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate the name and email fields from the linked User object
        # so the user sees their current values when they open the edit page.
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

        # Remove fields that don't apply to the user's role so the form
        # stays clean and relevant for each user type.
        if self.instance.role == 'employer':
            del self.fields['skills']
            del self.fields['availability']
            del self.fields['cv']
        else:
            del self.fields['company_name']
            del self.fields['company_description']
            del self.fields['website']


class RatingForm(forms.ModelForm):
    # Simple 1–5 star rating form. Rendered on the profile page for employers
    # who have worked with a job seeker and want to leave feedback.
    class Meta:
        model = Rating
        fields = ['score', 'comment']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-control',
                'placeholder': 'Share your experience working with this person...'
            }),
        }


class DocumentUploadForm(forms.Form):
    # Handles the document submission flow for job seeker verification.
    # None of the file fields are strictly required — users can upload
    # whichever documents they have — but legal name and phone are mandatory
    # because they're needed for the identity check.

    profile_photo = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png',
            'id': 'profile_photo'
        }),
        help_text='JPG or PNG, max 5MB'
    )

    dbs_check = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx',
            'id': 'dbs_check'
        }),
        help_text='PDF or Word document, max 10MB'
    )

    national_insurance = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,image/jpeg,image/png',
            'id': 'national_insurance'
        }),
        help_text='PDF, Word, or image, max 10MB'
    )

    work_permit_visa = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,image/jpeg,image/png',
            'id': 'work_permit_visa'
        }),
        help_text='PDF, Word, or image (if non-UK citizen), max 10MB'
    )

    legal_name = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your full legal name'
        })
    )

    phone_for_otp = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+44 7xxx xxxxxx',
            'type': 'tel'
        }),
        help_text='For OTP verification'
    )

    def clean(self):
        # Validate file sizes after the individual fields have been cleaned.
        # Each document type has its own size cap — profile photos are smaller
        # than the identity documents.
        cleaned_data = super().clean()

        doc_types = ['profile_photo', 'dbs_check', 'national_insurance', 'work_permit_visa']
        max_sizes = {
            'profile_photo': 5 * 1024 * 1024,       # 5MB
            'dbs_check': 10 * 1024 * 1024,          # 10MB
            'national_insurance': 10 * 1024 * 1024,  # 10MB
            'work_permit_visa': 10 * 1024 * 1024,   # 10MB
        }

        for doc_type in doc_types:
            file = cleaned_data.get(doc_type)
            if file and file.size > max_sizes[doc_type]:
                self.add_error(
                    doc_type,
                    f'File too large. Max {max_sizes[doc_type] / 1024 / 1024}MB'
                )

        return cleaned_data
