import datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager # type: ignore
from django.db import models  # type: ignore
from django.utils import timezone # type: ignore

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )
        user.set_password(password)  # Hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(
            username,
            email,
            password
        )
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    last_login = models.DateTimeField(null=True, blank=True)  # Add this line
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # Add if you want users to access the admin site
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']


class Parent(models.Model):
    # Other fields...
    auto_generated_username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    auto_generated_password = models.CharField(max_length=128, blank=True, null=True)  # Optional: Store plain password
    student_username = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return f"Parent of {self.student_username}"

    # Other fields...

from django.contrib.auth.models import User # type: ignore

class Teacher(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    age = models.IntegerField()
    email = models.EmailField()
    contact = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    teaching_area = models.CharField(max_length=255, blank=True, null=True)
    classes = models.CharField(max_length=255, blank=True, null=True)
    subjects = models.CharField(max_length=255, blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    referral = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Track approval status
    auto_generated_username = models.CharField(max_length=150, unique=True, null=True)
    auto_generated_password = models.CharField(max_length=128, null=True)  # Store hashed passwords


    def __str__(self):
        return f"{self.first_name} {self.last_name}"



class ContactMessage(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    tel = models.CharField(max_length=15, blank=True, null=True)
    message = models.TextField()
    replied = models.BooleanField(default=False)  # New field to track if a reply has been sent

    def __str__(self):
        return f'Message from {self.first_name} {self.last_name}'


class Course(models.Model):
    course_name = models.CharField(max_length=255, default='Default Course Name')
    description = models.TextField()
    duration = models.IntegerField(default=4)  # Setting default duration to 4 weeks

    def __str__(self):
        return self.course_name


class ClassSchedule(models.Model):
    class_name = models.CharField(max_length=100)  
    course_name = models.ForeignKey(Course, on_delete=models.CASCADE)  
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    meeting_link = models.URLField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    

    def __str__(self):
        return f"{self.class_name} ({self.course_name}) by {self.teacher} on {self.date}"
    

class Material(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    file = models.FileField(upload_to='materials/')
    description = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
    

from django.db import models # type: ignore
from django.utils import timezone # type: ignore
from .models import Teacher

class TeacherInterview(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='interviews')
    interview_date = models.DateField()
    starting_time = models.TimeField()
    ending_time = models.TimeField()
    meeting_link = models.URLField(max_length=200)
    interviewer_name = models.CharField(max_length=150)
    notes = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"Interview for {self.teacher.first_name} {self.teacher.last_name} on {self.interview_date}"



from .models import Course, Teacher

class Quizs(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.title} - {self.course.course_name}"
 
class Question(models.Model):
    quiz = models.ForeignKey(Quizs, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=300)
    option_a = models.CharField(max_length=100)
    option_b = models.CharField(max_length=100)
    option_c = models.CharField(max_length=100)
    option_d = models.CharField(max_length=100)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.CharField(max_length=255) 

from .models import CustomUser  # Import your custom user model

class UserAnswer(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Direct reference to the custom user model
    quiz = models.ForeignKey(Quizs, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField()
    submitted_at = models.DateTimeField(auto_now_add=True)

class UserAnswers(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='user_answers', on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
     
    def __str__(self):
        return f"{self.user.username} - {self.question.text}: {self.selected_option}"


from django.db import models # type: ignore
from django.utils import timezone # type: ignore

class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    file = models.FileField(upload_to='assignments/', null=True, blank=True)
    course_name = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='assignments')
    
    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    file = models.FileField(upload_to='submissions/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # New field for grade

    def __str__(self):
        return f"Submission by {self.student} for {self.assignment}"
    

from django.db import models

class FeedbackQuestion(models.Model):
    question_text = models.TextField()

    def __str__(self):
        return self.question_text


class Feedback(models.Model):
    user = models.CharField(max_length=255)  # Use custom_user_id from the session
    question = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE)
    response = models.CharField(
        max_length=20,
        choices=[
            ('strongly_agree', 'Strongly Agree'),
            ('agree', 'Agree'),
            ('neutral', 'Neutral'),
            ('disagree', 'Disagree'),
            ('strongly_disagree', 'Strongly Disagree'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.question} - {self.response}"


class CalendarEvent(models.Model):
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=50)  # e.g., 'class', 'assignment', 'exam'
    course = models.ForeignKey(Course, on_delete=models.CASCADE)  # Link event to a course
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)  # Link the event to the Teacher

    def __str__(self):
        return self.title