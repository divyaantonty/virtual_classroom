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
        
        if not (username.isalpha() or username.isdigit()):
            messages.error(request, "Username should contain only alphabets or only digits, not both.")
            return redirect('register')

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


from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactMessageForm  # Adjust the import based on your structure

def contact_view(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()  # Save the form data to the database
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('index')  # Redirect to the index page after submitting
        else:
            # This line ensures that the form with error messages is re-rendered
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactMessageForm()

    return render(request, 'contact.html', {'form': form})  # Replace 'your_template.html' with your actual template name


from django.shortcuts import render, redirect
from .models import ContactMessage
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

# View to display all contact messages
def view_messages(request):
    messages_list = ContactMessage.objects.all()
    return render(request, 'view_messages.html', {'messages_list': messages_list})

def reply_message(request, message_id):
    message_obj = ContactMessage.objects.get(id=message_id)
    if request.method == 'POST':
        subject = 'Thank you for contacting us'
        body = 'We will contact you for more clarification regarding your query.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [message_obj.email]

        send_mail(subject, body, from_email, recipient_list)

        # Update the replied status
        message_obj.replied = True
        message_obj.save()

        messages.success(request, 'Reply sent successfully!')
        return redirect('view_messages')
    return redirect('view_messages')



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

from django.shortcuts import render
from .models import CustomUser

def manage_students(request):
    students = CustomUser.objects.select_related('course').filter(is_active=1)

    past_students = CustomUser.objects.filter(is_active=0)
    return render(request, 'manage_students.html', {'students': students, 'past_students':past_students})


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import CustomUser

def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id)
    if request.method == 'POST':
        student.is_active = 0  
        student.save()  
        messages.success(request, 'Student marked as active successfully.')
        return redirect('manage_students')




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

from django.shortcuts import render, redirect
from .models import Teacher  # Adjust the import based on your app structure

def view_profile(request):
    teacher_id = request.session.get('teacher_id')
    
    if not teacher_id:
        print("No teacher ID found in session.")  # Debugging line
        return render(request, 'view_profile.html', {'error': 'Profile not found.'})
    
    try:
        teacher = Teacher.objects.get(id=teacher_id)
        print(f"Logged in teacher's username: {teacher.auto_generated_username}")  # Debugging line
        context = {'teacher': teacher}
    except Teacher.DoesNotExist:
        print("No matching Teacher found.")  # Debugging line
        context = {'error': 'Profile not found.'}
    
    return render(request, 'view_profile.html', context)

from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Teacher
import random
import string

def manage_teachers(request):
    pending_teachers = Teacher.objects.filter(status='pending')
    approved_teachers = Teacher.objects.filter(status='approved')
    
    context = {
        'pending_teachers': pending_teachers,
        'approved_teachers': approved_teachers,
    }
    return render(request, 'manage_teachers.html', context)

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


from django.shortcuts import render, redirect, get_object_or_404
from .models import Teacher

def reject_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == 'POST':
        teacher.delete()  # Or you can set the status to 'pending'
        return redirect('manage_teachers')  # Redirect after rejection

    return render(request, 'reject_teacher.html', {'teacher': teacher})

def approving_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == 'POST':
        # Update the teacher's status to 'approved'
        teacher.status = 'approved'
        teacher.save()
        messages.success(request, f'Teacher {teacher.first_name} {teacher.last_name} has been approved.')

        return redirect('manage_teachers')  # Redirect to the management page after approval

    # If GET request, render the approve form
    form = None  # You can add additional form processing logic if required
    return render(request, 'approve_teacher.html', {'teacher': teacher, 'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Teacher

# View to handle deleting a teacher
def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == 'GET':
        teacher.delete()
        messages.success(request, f'Teacher {teacher.first_name} {teacher.last_name} has been deleted.')
        return redirect('manage_teachers')


from django.shortcuts import render
from .models import Teacher

def teacher_list(request):
    teachers = Teacher.objects.all()  # Fetch all teachers from the database
    return render(request, 'teacher_list.html', {'teachers': teachers})


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Course
from .forms import CourseForm
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()  
            messages.success(request, 'Course added successfully!')
            return redirect('course_list')  
        else:
            messages.error(request, 'Failed to add the course. Please correct the errors.')
    else:
        form = CourseForm()

    return render(request, 'add_courses.html', {'form': form})


def course_list(request):
    courses = Course.objects.all()  
    return render(request, 'course_list.html', {'courses': courses})

from django.shortcuts import render, redirect
from .models import Course, ClassSchedule, Teacher
from datetime import date, datetime, timezone

def schedule_class(request):
    teacher_id = request.session.get('teacher_id')  
    if not teacher_id:
        return redirect('login')  
    
    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return redirect('login')  

    courses = Course.objects.all()  
    today = date.today() 
    error_message = None  
    if request.method == 'POST':
        class_name = request.POST.get('class_name')
        course_id = request.POST.get('course')
        selected_date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        meeting_link = request.POST.get('meeting_link')

        
        if selected_date < today.isoformat():
            return render(request, 'schedule_class.html', {
                'courses': courses,
                'today': today,
                'error_message': "The selected date cannot be in the past."
            })

        course = Course.objects.get(id=course_id)  
        class_schedule = ClassSchedule.objects.create(
            class_name=class_name,
            course_name=course,
            date=selected_date,
            start_time=start_time,
            end_time=end_time,
            meeting_link=meeting_link,
            teacher=teacher  
        )

        return redirect('schedule_class')  
    current_datetime = datetime.now()
    scheduled_classes = ClassSchedule.objects.filter(teacher=teacher, end_time__gt=current_datetime)

    return render(request, 'schedule_class.html', {
        'courses': courses,
        'today': today,
        'scheduled_classes': scheduled_classes,
        'error_message': error_message
    })

    

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import ClassSchedule, Teacher  # Make sure to import the Teacher model

def view_teacher_schedule_class(request):
    # Retrieve the teacher's ID from the session
    teacher_id = request.session.get('teacher_id')

    # Check if the teacher ID exists in the session
    if not teacher_id:
        return redirect('login')  # Redirect to login if the teacher ID is not set

    try:
        # Retrieve the teacher object using the ID from the session
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return redirect('login')  # Redirect to login if the teacher does not exist

    # Get the current date and time
    current_time = timezone.now()

    # Filter classes that are ongoing or scheduled for the future for the logged-in teacher
    future_classes = ClassSchedule.objects.filter(
        Q(date__gt=current_time.date()) |  # Future dates
        (Q(date=current_time.date()) & Q(end_time__gt=current_time.time()))  # Today with end time in the future
    ).filter(teacher_id=teacher_id)  # Filter by teacher ID

    # Log filtered future classes for debugging
    print(f"Future Classes for teacher ID {teacher_id}: {future_classes}")

    # Store some custom session data if needed (optional)
    request.session['last_viewed'] = str(current_time)

    context = {
        'future_classes': future_classes,
        'last_viewed': request.session.get('last_viewed')  # Accessing session data (optional)
    }

    return render(request, 'view_teacher_schedule_class.html', context)




from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ClassSchedule, CustomUser
from django.utils import timezone
from django.db.models import Q

def view_scheduled_classes(request):
    # Retrieve the custom user ID from the session
    custom_user_id = request.session.get('custom_user_id')

    if not custom_user_id:
        messages.error(request, "You are not logged in.")
        return redirect('login')

    try:
        # Fetch the student (CustomUser) based on the custom user ID
        student = CustomUser.objects.get(id=custom_user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('login')

    # Check if the student is registered for a course
    registered_course = student.course
    if not registered_course:
        messages.error(request, "You are not registered for any course.")
        return redirect('student_dashboard')

    # Get the current date and time
    current_datetime = timezone.now()

    # Fetch scheduled classes for the registered course that are ongoing or in the future
    scheduled_classes = ClassSchedule.objects.filter(
        course_name=registered_course,
    ).filter(
        # Include classes that are ongoing or scheduled for future dates
        Q(date=current_datetime.date(), start_time__lte=current_datetime.time(), end_time__gte=current_datetime.time()) |  # Classes that are ongoing
        Q(date__gt=current_datetime.date())  # Classes scheduled for future dates
    ).order_by('date', 'start_time')  # Sort classes by date and start time

    # Check if there are any scheduled classes
    if not scheduled_classes.exists():
        messages.info(request, "No upcoming scheduled classes for your registered course.")
        return render(request, 'view_scheduled_classes.html', {'scheduled_classes': scheduled_classes})

    # Pass the scheduled classes to the template
    return render(request, 'view_scheduled_classes.html', {'scheduled_classes': scheduled_classes})



from django.shortcuts import render, redirect
from .models import CustomUser, ClassSchedule, Parent

def view_class_schedule(request):
    parent_id = request.session.get('parent_id')
    
    if not parent_id:
        
        return redirect('login')
    
    try:
        parent = Parent.objects.get(id=parent_id)
    except Parent.DoesNotExist:
       
        return redirect('error_page')

    child_username = parent.student_username
    child = CustomUser.objects.get(username=child_username)
    child_schedule = ClassSchedule.objects.filter(course_name=child.course)

    context = {
        'child': child,
        'child_schedule': child_schedule,
    }
    
    return render(request, 'view_class_schedule.html', context)


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser, Parent, Teacher
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Parent


def change_password(request):
    parent_id = request.session.get('parent_id')
    
    # Check if parent is logged in
    if not parent_id:
        messages.error(request, 'You are not logged in as a parent.')
        return redirect('login')

    try:
        # Fetch the parent instance
        parent = Parent.objects.get(id=parent_id)
    except Parent.DoesNotExist:
        messages.error(request, 'Parent not found.')
        return redirect('login')

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password')
        new_password2 = request.POST.get('confirm_password')

        # Check if new passwords match
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')

        # Check if the old password is correct
        if old_password != parent.auto_generated_password:
            messages.error(request, 'Old password is incorrect.')
            return redirect('change_password')

        # Update the password in the database
        parent.auto_generated_password = new_password1
        parent.save()
        messages.success(request, 'Your password has been successfully updated.')
        return redirect('login')

    return render(request, 'change_password.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .models import CustomUser, Parent, Teacher
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Teacher

def teacher_changepassword(request):
    teacher_id = request.session.get('teacher_id')
    
    # Check if teacher is logged in
    if not teacher_id:
        messages.error(request, 'You are not logged in as a teacher.')
        return redirect('login')

    try:
        # Fetch the teacher instance
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher not found.')
        return redirect('login')

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password')
        new_password2 = request.POST.get('confirm_password')

        # Check if new passwords match
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
            return redirect('teacher_changepassword')

        # Check if the old password is correct
        if old_password != teacher.auto_generated_password:
            messages.error(request, 'Old password is incorrect.')
            return redirect('teacher_changepassword')

        # Update the password in the database
        teacher.auto_generated_password = new_password1
        teacher.save()
        messages.success(request, 'Your password has been successfully updated.')
        return redirect('login')

    return render(request, 'teacher_changepassword.html')



from django.shortcuts import render, redirect, get_object_or_404
from .models import Teacher
from django.contrib import messages

def teacher_updateprofile(request):
    teacher_id = request.session.get('teacher_id')
    
    if not teacher_id:
        messages.error(request, 'No teacher ID found in session.')
        return redirect('login')

    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == 'POST':
        # Fetch the form data
        teacher.first_name = request.POST.get('first_name')
        teacher.last_name = request.POST.get('last_name')
        teacher.gender = request.POST.get('gender')
        teacher.age = request.POST.get('age')
        teacher.auto_generated_username = request.POST.get('auto_generated_username')
        teacher.email = request.POST.get('email')
        teacher.contact = request.POST.get('contact')
        teacher.address_line1 = request.POST.get('address_line1')
        teacher.address_line2 = request.POST.get('address_line2')
        teacher.city = request.POST.get('city')
        teacher.state = request.POST.get('state')
        teacher.zip_code = request.POST.get('zip_code')
        teacher.qualification = request.POST.get('qualification')
        teacher.teaching_area = request.POST.get('teaching_area')
        teacher.classes = request.POST.get('classes')
        teacher.subjects = request.POST.get('subjects')
        teacher.experience = request.POST.get('experience')
        teacher.referral = request.POST.get('referral')

        # Save the updated teacher details
        teacher.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('view_profile')  

    context = {'teacher': teacher}
    return render(request, 'teacher_updateprofile.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from .models import Parent
from django.contrib import messages
def parent_update_profile(request):
    parent_id = request.session.get('parent_id')
    
    if not parent_id:
        messages.error(request, 'No parent ID found in session.')
        return redirect('login')

    parent = get_object_or_404(Parent, id=parent_id)

    if request.method == 'POST':
        # Fetch the form data
        parent.auto_generated_username = request.POST.get('auto_generated_username')
        

        # Save the updated teacher details
        parent.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('parent_dashboard')  

    context = {'parent': parent}
    return render(request, 'parent_update_profile.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from .models import Material, Course, Teacher

def upload_material(request):
    if request.method == 'POST':
        course_id = request.POST.get('course') 
        description = request.POST.get('description')  
        file = request.FILES.get('file') 

       
        if course_id and file:
            course = Course.objects.get(id=course_id)
            
            teacher_id = request.session.get('teacher_id')
            if teacher_id:
                teacher = get_object_or_404(Teacher, id=teacher_id)  

                Material.objects.create(
                    teacher=teacher,  # Use the logged-in teacher from session
                    course=course,
                    file=file,
                    description=description
                )
                return redirect('teacher_dashboard')  # Redirect to dashboard after upload

    # Fetch the list of courses to display in the form
    courses = Course.objects.all()
    
    return render(request, 'upload_material.html', {'courses': courses})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Material, CustomUser

def view_materials(request):
    # Check if a CustomUser (student) is logged in by checking session
    custom_user_id = request.session.get('custom_user_id')
    
    if not custom_user_id:
        messages.error(request, 'You must be logged in as a student to view materials.')
        return redirect('login')  # Redirect to login page if no session

    # Fetch the CustomUser (student) object using the session ID
    custom_user = get_object_or_404(CustomUser, id=custom_user_id)

    # Ensure the student is registered for a course
    course = custom_user.course
    if not course:
        messages.error(request, 'You are not registered for any course.')
        return redirect('student_dashboard')  # Redirect if no course is associated

    # Get materials related to the student's course
    materials = Material.objects.filter(course=course)

    return render(request, 'view_materials.html', {'materials': materials})


# views.py
from django.shortcuts import render, get_object_or_404
from .models import Material, Parent, CustomUser

def view_study_materials(request):

    parent = get_object_or_404(Parent, auto_generated_username=request.user.username)
    
    student = get_object_or_404(CustomUser, username=parent.student_username)

    materials = Material.objects.filter(course=student.course)
    
    return render(request, 'view_study_materials.html', {'materials': materials, 'student': student})

