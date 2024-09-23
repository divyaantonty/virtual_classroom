import uuid
import re
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import CustomUser, Course, Parent

def register(request):
    if request.method == 'POST':
        # Extract form data from request.POST
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        course_id = request.POST.get('course')

        # Perform basic validation
        if not all([username, email, password, confirm_password, course_id]):
            messages.error(request, 'Please fill out all fields.')
            return render(request, 'register.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html')

        # Check if the username or email is unique for the student
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
            return render(request, 'register.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return render(request, 'register.html')

        # Validate email format
        try:
            validate_email(email)
            if not email.endswith('@gmail.com'):
                raise ValidationError('Email must be in Gmail format.')
        except ValidationError as e:
            messages.error(request, f'Invalid email: {e.message}')
            return render(request, 'register.html')

        # Validate password complexity
        if not re.fullmatch(r'^(?=.*[A-Z])(?=.*\d)(?=.*[a-zA-Z])(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$', password):
            messages.error(request, 'Password must contain at least 6 characters, including 1 uppercase letter, 1 number, and 1 special character.')
            return render(request, 'register.html')

        # Fetch the selected course
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            messages.error(request, 'Selected course does not exist.')
            return render(request, 'register.html')

        # Create and save student user instance
        student_user = CustomUser(
            username=username,
            email=email,
            course=course,  # Save the selected course
            password=make_password(password),  
            
        )
        student_user.save()

        # Auto-generate a unique parent username using UUID
        parent_username = f'parent_{uuid.uuid4().hex[:8]}'  # Generate an 8-character unique username

        # Generate a random secure password for the parent
        parent_password = get_random_string(12)  # Generate a 12-character password
        # After creating the student_user
        parent = Parent.objects.create(
            auto_generated_username=parent_username,
            auto_generated_password=parent_password,
            student_username=student_user.username  # Link to the student's username
        )

        # Send email with parent's auto-generated credentials to the student's email
        send_mail(
            subject='Registration Successful: Parent Login Credentials',
            message=f'You have successfully registered.\n\n'
                    f'Your parent\'s login details:\n'
                    f'Username: {parent_username}\n'
                    f'Password: {parent_password}\n',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],  # Send to the student's email
            fail_silently=False,
        )

        messages.success(request, 'Account created successfully! Parent login credentials have been sent to your email.')
        return redirect('login')
    else:
        # Fetch all courses to display in the registration form
        courses = Course.objects.all()
        return render(request, 'register.html', {'courses': courses})


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Teacher, Parent, CustomUser

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check Teacher model
        try:
            teacher = Teacher.objects.get(auto_generated_username=username)
            if teacher.auto_generated_password == password:
                # Manually log in the teacher (using sessions)
                request.session['teacher_id'] = teacher.id  # Store teacher ID in session
                return redirect('teacher_dashboard')
        except Teacher.DoesNotExist:
            pass  # Not a teacher

        # Check Parent model
        try:
            parent = Parent.objects.get(auto_generated_username=username)
            if parent.auto_generated_password == password:
                # Manually log in the parent (using sessions)
                request.session['parent_id'] = parent.id  # Store parent ID in session
                return redirect('parent_dashboard')
        except Parent.DoesNotExist:
            pass  # Not a parent

        # Check CustomUser model
        try:
            custom_user = CustomUser.objects.get(username=username)
            if custom_user.check_password(password):  # Assuming password is stored as plaintext
                # Manually log in the CustomUser (using sessions)
                request.session['custom_user_id'] = custom_user.id  # Store CustomUser ID in session
                return redirect('student_dashboard')
            else:
                messages.error(request, 'Invalid password for CustomUser.')
        except CustomUser.DoesNotExist:
            pass  # Not a CustomUser

        # If no match, show an error message
        messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')

# Dashboard views

def student_dashboard(request):
    custom_user_id = request.session.get('custom_user_id')
    if not custom_user_id:
        return redirect('login')  # Redirect to login if CustomUser not authenticated
    # Fetch the CustomUser object based on the session ID
    try:
        custom_user = CustomUser.objects.get(id=custom_user_id)
    except CustomUser.DoesNotExist:
        return redirect('login')  # Redirect if the user doesn't exist

    # Pass the CustomUser object to the template
    return render(request, 'student_dashboard.html', {'custom_user': custom_user})

def teacher_dashboard(request):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('login')  # Redirect to login if teacher not authenticated

    # Fetch the Teacher object using teacher_id
    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return redirect('login')  # Redirect if the teacher doesn't exist

    # Pass the teacher object to the template
    return render(request, 'teacher_dashboard.html', {
        'first_name': teacher.first_name,
        'last_name': teacher.last_name
    })

def parent_dashboard(request):
    parent_id = request.session.get('parent_id')
    if not parent_id:
        return redirect('login')  # Redirect to login if parent not authenticated

    # Fetch parent object based on the session ID
    try:
        parent = Parent.objects.get(id=parent_id)

        # Fetch the student using the username stored in the Parent model
        student = CustomUser.objects.get(username=parent.student_username)
    except Parent.DoesNotExist:
        return redirect('login')
    except CustomUser.DoesNotExist:
        student = None  # Handle if the student doesn't exist

    # Pass the parent and student to the template
    return render(request, 'parent_dashboard.html', {'parent': parent, 'student': student})


def index_view(request):
    return render(request, 'index.html')

def about_view(request):
    return render(request, 'about.html')

def admissions_view(request):
    return render(request, 'admissions.html')

# views.py
from django.shortcuts import render, redirect
from .forms import ContactMessageForm
from .models import ContactMessage

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactMessageForm  # Adjust the import based on your structure

def contact_view(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()  # Save the form data to the database
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('index') # Redirect to the index page after submitting
        else:
            form = ContactMessageForm()
    else:
        form = ContactMessageForm()

    return render(request, 'contact.html', {'form': form})

from django.contrib.admin.views.decorators import staff_member_required
from .models import ContactMessage

def view_message(request):
    return render(request, 'view_messages.html')


def courses_view(request):
    return render(request, 'courses.html')

def course_detail_10(request):
    return render(request, 'course_detail_10.html')

def course_detail_higher_secondary(request):
    return render(request, 'course_detail_higher_secondary.html')

def teachers_view(request):
    return render(request, 'teachers.html')

def recover_view(request):
    return render(request, 'recover.html')

def features(request):
    return render(request, 'features.html')

def parent(request):
    return render(request, 'parent.html')

from django.shortcuts import render, redirect
from django.contrib import messages

def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Check against predefined credentials
        if username == 'admin' and password == 'admin123':
            # Create a custom session for the admin user
            request.session['is_admin'] = True
            return redirect('admin_dashboard')  # Redirect to admin dashboard
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    
    return render(request, 'admin_login.html')

def admin_dashboard(request):   
    return render(request, 'admin_dashboard.html')

def manage_students(request):
    return render(request, 'manage_students.html')

from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect

def logout(request):
    auth_logout(request)
    request.session.flush()  
    return redirect('login')


def recover(request):
    return render(request, 'recover.html')
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
from django.contrib.auth.views import PasswordResetDoneView

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
from django.contrib.auth.views import PasswordResetCompleteView

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import TeacherRegistrationForm  # Assuming you've created a form
from .models import Teacher

def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.status = 'pending'  # Set status as pending
            teacher.save()

            # Add a success message
            messages.success(request, "You have successfully registered!")

            # Redirect to the about page
            return redirect('login')
    else:
        form = TeacherRegistrationForm()
    
    return render(request, 'register_teacher.html', {'form': form})



from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Teacher
import random
import string

def manage_teachers(request):
    pending_teachers = Teacher.objects.filter(status='pending')
    all_teachers = Teacher.objects.all()
    return render(request, 'manage_teachers.html', {
        'pending_teachers': pending_teachers,
        'all_teachers': all_teachers,
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import Teacher
from .forms import ApproveTeacherForm

def approve_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    if request.method == 'POST':
        form = ApproveTeacherForm(request.POST, instance=teacher)
        
        if form.is_valid():
            if teacher.status != 'approved':  # Check if already approved
                teacher.status = 'approved'  # Update status to approved
                teacher.save()

                # Debugging: Check if teacher is approved
                print(f"Teacher {teacher.first_name} {teacher.last_name} is now approved")
             
                # Generate random username and password
                random_username = f"teacher_{get_random_string(8)}"  # Example username
                random_password = get_random_string(8)  # Random password

 
                # Debugging: Check if credentials are generated
                print(f"Generated credentials: {random_username}, {random_password}")
                # Save the credentials in the Teacher model
                teacher.auto_generated_username = random_username
                teacher.auto_generated_password = random_password  # Store plain password
                teacher.user = User  # Link the user instance
                teacher.save()

                # Send email to the teacher
                subject = 'Your Teacher Account has been Approved'
                message = (
                    f"Dear {teacher.first_name} {teacher.last_name},\n\n"
                    f"Your account has been approved! Here are your login details:\n\n"
                    f"Username: {random_username}\n"
                    f"Password: {random_password}\n\n"
                    "Please log in and change your password upon your first login.\n\n"
                    "Best Regards,\n"
                    "The Administration Team"
                )

                # Send the email
                send_mail(
                    subject,
                    message,
                    'divyaantony2025@mca.ajce.in',  # Replace with your admin email
                    [teacher.email],
                    fail_silently=False,
                )

                return redirect('teacher_list')  # Redirect to the teacher list or another page
            else:
                # Debugging: If teacher is already approved
                print("Teacher is already approved")
        else:
            # Debugging: Show form errors if validation fails
            print(form.errors)
    
    else:
        form = ApproveTeacherForm(instance=teacher)
    
    return render(request, 'approve_teacher.html', {'form': form, 'teacher': teacher})


def reject_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher.status = 'rejected'
    teacher.save()
    return redirect('approve_teacher')

def remove_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher.delete()
    return redirect('manage_teachers')

from django.shortcuts import render
from .models import Teacher

def teacher_list(request):
    teachers = Teacher.objects.all()  # Fetch all teachers from the database
    return render(request, 'teacher_list.html', {'teachers': teachers})


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Course
from .forms import CourseForm  # Assuming you are using a form to handle input

def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new course to the database
            messages.success(request, 'Course added successfully!')
            return redirect('course_list')  # Redirect to the same page or another page
        else:
            messages.error(request, 'Failed to add the course. Please correct the errors.')
    else:
        form = CourseForm()

    return render(request, 'add_courses.html', {'form': form})


def course_list(request):
    courses = Course.objects.all()  # Fetch all courses
    return render(request, 'course_list.html', {'courses': courses})

from django.shortcuts import render, redirect
from .models import Course, ClassSchedule, Teacher

def schedule_class(request):
    teacher_id = request.session.get('teacher_id')  # Fetch the teacher_id from session
    if not teacher_id:
        return redirect('login')  # Redirect to login if teacher not authenticated

    # Fetch the Teacher object using teacher_id from session
    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return redirect('login')  # Redirect if the teacher doesn't exist

    courses = Course.objects.all()  # Fetch all courses

    if request.method == 'POST':
        class_name = request.POST.get('class_name')
        course_id = request.POST.get('course')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        meeting_link = request.POST.get('meeting_link')

        course = Course.objects.get(id=course_id)  # Get the selected course
        class_schedule = ClassSchedule.objects.create(
            class_name=class_name,
            course_name=course,
            date=date,
            start_time=start_time,
            end_time=end_time,
            meeting_link=meeting_link,
            teacher=teacher  # Assign the teacher using the teacher object from session
        )

        return redirect('schedule_class')  # Redirect to class list view or appropriate page

    return render(request, 'schedule_class.html', {'courses': courses})

from django.shortcuts import render, redirect
from .models import ClassSchedule

def student_view_classes(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if the user is not authenticated

    student = request.user  # Get the logged-in user (instance of CustomUser)

    # Store additional data in the session if needed
    request.session['student_username'] = student.username

    # Fetch scheduled classes for the student's course
    scheduled_classes = ClassSchedule.objects.filter(course_name=student.course).order_by('date')

    return render(request, 'student/view_classes.html', {
        'scheduled_classes': scheduled_classes,
        'student': student
    })
