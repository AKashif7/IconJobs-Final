from django import forms
from .models import Job, Application, JobCategory


class JobPostForm(forms.ModelForm):
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
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class ApplicationForm(forms.ModelForm):
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
    category = forms.ModelChoiceField(
        queryset=JobCategory.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )