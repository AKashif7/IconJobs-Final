from django import forms
from .models import Job, Application, JobCategory


class JobPostForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'category', 'location', 'duration',
                  'pay_rate', 'pay_type', 'spots_available', 'start_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe the job tasks, expectations, and any requirements...'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Soho, London'}),
        }


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_message']
        widgets = {
            'cover_message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Introduce yourself and explain why you are a great fit for this role...'
            }),
        }
        labels = {
            'cover_message': 'Message to Employer (Optional)',
        }


class JobSearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search jobs...'}))
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Location'}))
    duration = forms.ChoiceField(
        choices=[('', 'Any Duration')] + list(Job.DURATION_CHOICES),
        required=False
    )
    category = forms.ModelChoiceField(
        queryset=JobCategory.objects.all(),
        required=False,
        empty_label='All Categories'
    )
