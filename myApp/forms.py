# forms.py
from django import forms

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)

from .models import Teacher

class TeacherRegistrationForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'first_name',
            'last_name',
            'gender',
            'age',
            'email',
            'contact',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'zip_code',
            'qualification',
            'teaching_area',
            'classes',
            'subjects',
            'experience',
            'referral',
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'gender': forms.Select(choices=Teacher.GENDER_CHOICES),
            'age': forms.NumberInput(attrs={'placeholder': 'e.g., 23'}),
            'email': forms.EmailInput(attrs={'placeholder': 'myname@example.com'}),
            'contact': forms.TextInput(attrs={'placeholder': '(000) 000-0000'}),
            'address_line1': forms.TextInput(attrs={'placeholder': 'Street Address'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Street Address Line 2'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'placeholder': 'State / Province'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'Postal / Zip Code'}),
            'qualification': forms.TextInput(),
            'teaching_area': forms.TextInput(),
            'classes': forms.TextInput(),
            'subjects': forms.TextInput(),
            'experience': forms.Textarea(),
            'referral': forms.TextInput(attrs={'placeholder': 'E.g. Ads, Friend, Internet'}),
        }


from .models import ContactMessage

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['first_name', 'last_name', 'email', 'tel', 'message']

from django import forms
from .models import Teacher

class ApproveTeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['status']  # You can include other fields if needed


from .models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_name', 'description', 'duration']



