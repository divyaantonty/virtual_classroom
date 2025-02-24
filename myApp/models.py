import datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager # type: ignore
from django.db import models  # type: ignore
from django.utils import timezone # type: ignore
from datetime import timedelta

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
    first_name = models.CharField(max_length=100, blank=True, null=True)  # Added from Student model
    last_name = models.CharField(max_length=100, blank=True, null=True)   # Added from Student model
    date_of_birth = models.DateField(blank=True, null=True)               # Added from Student model
    contact = models.CharField(max_length=15, blank=True, null=True)      # Added from Student model
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # Explicit superuser field
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
from datetime import date

class Teacher(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(default=date.today)
    email = models.EmailField()
    contact = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    qualification_certificate = models.FileField(upload_to='certificates/qualifications/', blank=True, null=True)
    experience_certificate = models.FileField(upload_to='certificates/experience/', blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Track approval status
    auto_generated_username = models.CharField(max_length=150, unique=True, null=True)
    auto_generated_password = models.CharField(max_length=128, null=True)  # Store hashed passwords
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TeacherCourse(models.Model):
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='teacher_courses')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='course_teachers')
    teaching_area = models.CharField(max_length=255) 
    class Meta:
        unique_together = ('teacher', 'course')
        
class ContactMessage(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    tel = models.CharField(max_length=15, blank=True, null=True)
    message = models.TextField()
    replied = models.BooleanField(default=False)  # New field to track if a reply has been sent

    def __str__(self):
        return f'Message from {self.first_name} {self.last_name}'


from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from datetime import timedelta
from django.db.models import Avg

class Course(models.Model):
    course_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)
    description = models.TextField()
    duration = models.IntegerField(default=4)  # in weeks
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    starting_date = models.DateField(default=date.today)
    ending_date = models.DateField(blank=True, null=True)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    def update_average_rating(self):
        average_rating = self.ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
        self.rating = round(average_rating, 2) if average_rating else None
        self.save()

    def __str__(self):
        return self.course_name



class Enrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    enrollment_time = models.TimeField(auto_now_add=True)  # Store time of enrollment
    completion_date = models.DateField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')], default='Pending')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)  # Store the payment amount
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # Store the payment transaction ID
    payment_date = models.DateField(blank=True, null=True)  # Date when payment was completed
    
    def __str__(self):
        return f"{self.student} enrolled in {self.course}"


class CourseRating(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, null=True)
    date_rated = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the average rating of the course after saving a new rating
        self.course.update_average_rating()

    def __str__(self):
        return f"Rating of {self.rating} for {self.course.course_name} by {self.student}"

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
    duration = models.IntegerField(default=30, help_text="Duration of the quiz in minutes")

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


class UserAnswers(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='user_answers', on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # To store marks
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Optional: store percentage
    grade = models.CharField(max_length=10, null=True, blank=True)  # Optional: store grade
    attempt_date = models.DateTimeField(null=True, blank=True, auto_now_add=True)  # To track when the quiz was attempted

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
from django.utils.timezone import now  # Add this import

class FeedbackQuestion(models.Model):
    question_text = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='feedback_questions', null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
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
    event_type = models.CharField(max_length=50)  
    course = models.ForeignKey(Course, on_delete=models.CASCADE)  
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)  # Link the event to the Teacher

    def __str__(self):
        return self.title
    

from django.db import models
from django.utils import timezone

class Attendance(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    class_schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=[('present', 'Present'), ('absent', 'Absent')])

    def __str__(self):
        return f"{self.student} - {self.class_schedule.class_name} - {self.status}"

from django.db import models
from django.utils import timezone

class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    student = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, null=True, blank=True)
    leave_type = models.CharField(max_length=100, choices=(('sick', 'Sick'), ('personal', 'Personal')))
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.student.username}'s leave from {self.start_date} to {self.end_date}"
    


class Group(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='group')
    students = models.ManyToManyField(CustomUser, related_name='student_groups')  # For students only
    teachers = models.ManyToManyField(Teacher, related_name='teacher_groups')    # For teachers only

    def __str__(self):
        return f"Group for {self.course.course_name}"


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('voice', 'Voice Message'),
        ('video', 'Video Message'),
        ('image', 'Image Message'),
        ('pdf', 'PDF Document')
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField(null=True, blank=True)  # For text messages
    media_file = models.FileField(upload_to='chat_media/', null=True, blank=True)  # For voice/video files
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.message_type} by {self.sender.username} in {self.group.course.course_name}"
    

class TeacherMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('voice', 'Voice Message'),
        ('video', 'Video Message'),
        ('image', 'Image Message'),
        ('pdf', 'PDF Document')
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='teacher_messages')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    content = models.TextField(null=True, blank=True)
    media_file = models.FileField(upload_to='teacher_chat_media/', null=True, blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Teacher {self.teacher.first_name} {self.teacher.last_name} in {self.group.course.course_name}"

from django.db import models
from django.conf import settings
from .models import CalendarEvent

class EventRegistration(models.Model):
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('registered', 'Registered'), ('cancelled', 'Cancelled')],
        default='registered'
    )

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


# models.py
from django.db import models
from .models import Teacher, CustomUser

class TeacherStudent(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher', 'student')  # Prevent duplicate entries

class GeneratedQuestionPaper(models.Model):
    title = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to='question_papers/')
    answer_key_file = models.FileField(upload_to='answer_keys/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    total_marks = models.IntegerField()
    difficulty = models.CharField(max_length=50)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d')}"
    

class MaterialSummary(models.Model):
    material = models.OneToOneField(Material, on_delete=models.CASCADE, related_name='summary')
    summary_text = models.TextField()
    key_points = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for {self.material.description}"
    

from django.db import models
from django.conf import settings  # Import settings to reference CustomUser

class StudentFaceData(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    face_image = models.ImageField(upload_to='face_images/',default='default_face.jpg')  # Store actual image file
    is_face_captured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face data for {self.user.username}"

class FinalExam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    date_taken = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True)  # Track when student starts exam
    end_time = models.DateTimeField(null=True)    # Track when student finishes exam

    class Meta:
        unique_together = ['course', 'student']

class FinalExamQuestion(models.Model):
    exam = models.ForeignKey(FinalExam, on_delete=models.CASCADE)
    question_paper = models.ForeignKey(GeneratedQuestionPaper, on_delete=models.CASCADE)
    student_answer = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField(null=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    question_text = models.TextField()  # Store the actual question text
    answer_key = models.TextField()     # Store the answer key for this question

    def __str__(self):
        return f"Question for {self.exam.student} in {self.exam.course}"  


class ParentTeacherMessage(models.Model):
    MESSAGE_TYPES = [
        ('parent_to_teacher', 'Parent to Teacher'),
        ('teacher_to_parent', 'Teacher to Parent'),
    ]

    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='parent_messages')
    parent = models.ForeignKey('Parent', on_delete=models.CASCADE, related_name='teacher_messages')
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    subject = models.CharField(max_length=200, default="No Subject")

    class Meta:
        ordering = ['-date']
        verbose_name = "Parent-Teacher Message"
        verbose_name_plural = "Parent-Teacher Messages"

    def __str__(self):
        return f"Message from {self.get_sender()} to {self.get_receiver()}"

    def get_sender(self):
        return self.parent if self.message_type == 'parent_to_teacher' else self.teacher

    def get_receiver(self):
        return self.teacher if self.message_type == 'parent_to_teacher' else self.parent
    

class WhiteboardShare(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=50)
    whiteboard_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Whiteboard share by {self.teacher.first_name} for {self.course.course_name}"
    

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
class EventSuggestion(models.Model):
    parent = models.ForeignKey('Parent', on_delete=models.CASCADE, related_name='event_suggestions')
    student = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='event_suggestions')
    event = models.ForeignKey('CalendarEvent', on_delete=models.CASCADE, related_name='suggestions')
    suggestion_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Suggestion from {self.parent} for {self.student.username} - {self.event.title}"

class MindMap(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} - {self.student.username}"