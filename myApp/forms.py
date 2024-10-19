# forms.py
from django import forms

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)

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



