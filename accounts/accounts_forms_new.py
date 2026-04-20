from django import forms
from .models import UserDocument, VerificationQueue


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
