from django import forms
from .models import Job, Application, JobCategory

# Forms for the jobs app. Three forms cover everything: posting a job
# (employer), applying for a job (seeker), and filtering the job list
# (anyone browsing). All widgets are styled with Bootstrap classes so they
# match the rest of the site without extra CSS.


class JobPostForm(forms.ModelForm):
    # Used by employers on the Post a Job page and the Edit Job page.
    # The employer field isn't included here — it's set in the view from
    # request.user so an employer can't accidentally post as someone else.
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'category', 'location',
            'duration', 'pay_rate', 'pay_type', 'spots_available', 'start_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Warehouse Assistant, Event Staff, Kitchen Porter'
            }),
            'description': forms.Textarea(attrs={
                'rows': 7, 'class': 'form-control',
                'placeholder': 'Describe the role in detail — responsibilities, requirements, what the day looks like, what to wear, anything relevant...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Shoreditch, London'
            }),
            'duration': forms.Select(attrs={'class': 'form-select'}),
            'pay_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'pay_type': forms.Select(attrs={'class': 'form-select'}),
            'spots_available': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1'
            }),
            # date type makes the browser show a native date picker.
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class ApplicationForm(forms.ModelForm):
    # Only the cover message is collected from the applicant here. The job
    # and applicant are set in the view from the URL parameter and request.user.
    class Meta:
        model = Application
        fields = ['cover_message']
        widgets = {
            'cover_message': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': "Introduce yourself and explain why you're a great fit. Mention any relevant experience, your availability, and anything else the employer should know..."
            }),
        }


class JobSearchForm(forms.Form):
    # Powers the filter bar on the job listings page. All fields are optional
    # so users can search by keyword, location, duration, or category
    # individually or in any combination.
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Job title or keyword...'
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location'
        })
    )
    duration = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Any Duration'),
            ('2h', '2 Hours'),
            ('4h', '4 Hours'),
            ('8h', '8 Hours (full day)'),
            ('2d', '2 Days'),
            ('5d', '5 Days'),
            ('2w', '2 Weeks'),
            ('1m', '1 Month'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # ModelChoiceField automatically populates from the database so new
    # categories appear in the dropdown as soon as they're added in admin.
    category = forms.ModelChoiceField(
        queryset=JobCategory.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
