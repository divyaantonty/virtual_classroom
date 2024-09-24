from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

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

from django.contrib.auth.models import User

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
    
    def __str__(self):
        return f'Message from {self.first_name} {self.last_name}'

class Course(models.Model):
    course_name = models.CharField(max_length=255, default='Default Course Name')
    description = models.TextField()
    duration = models.IntegerField(default=4)  # Setting default duration to 4 weeks

    def __str__(self):
        return self.course_name


class ClassSchedule(models.Model):
    class_name = models.CharField(max_length=100)  # Optionally, you can give a custom name for the class.
    course_name = models.ForeignKey(Course, on_delete=models.CASCADE)  # Link to the selected course
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    meeting_link = models.URLField()  # URL for the meeting (e.g., Zoom link)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.class_name} ({self.course}) by {self.teacher.username} on {self.date}"