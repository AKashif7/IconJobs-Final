from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, Rating, UserDocument, VerificationQueue


class RegisterForm(UserCreationForm):
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
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
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
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(user=user, role=self.cleaned_data['role'])
        return user


class LoginForm(AuthenticationForm):
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
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        if self.instance.role == 'employer':
            del self.fields['skills']
            del self.fields['availability']
            del self.fields['cv']
        else:
            del self.fields['company_name']
            del self.fields['company_description']
            del self.fields['website']


class RatingForm(forms.ModelForm):
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
    """Form for uploading profile documents during registration or profile edit"""
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
        """Validate file sizes and types"""
        cleaned_data = super().clean()
        
        doc_types = ['profile_photo', 'dbs_check', 'national_insurance', 'work_permit_visa']
        max_sizes = {
            'profile_photo': 5 * 1024 * 1024,      # 5MB
            'dbs_check': 10 * 1024 * 1024,         # 10MB
            'national_insurance': 10 * 1024 * 1024, # 10MB
            'work_permit_visa': 10 * 1024 * 1024,  # 10MB
        }

        for doc_type in doc_types:
            file = cleaned_data.get(doc_type)
            if file and file.size > max_sizes[doc_type]:
                self.add_error(
                    doc_type,
                    f'File too large. Max {max_sizes[doc_type] / 1024 / 1024}MB'
                )

        return cleaned_data
