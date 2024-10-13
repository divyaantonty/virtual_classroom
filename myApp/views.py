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
from .models import CustomUser, Course, Parent, UserAnswers

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

from django.shortcuts import render, redirect
from .models import CustomUser, FeedbackQuestion, Feedback

def student_dashboard(request):
    custom_user_id = request.session.get('custom_user_id')
    if not custom_user_id:
        return redirect('login')  # Redirect to login if CustomUser not authenticated

    # Fetch the CustomUser object based on the session ID
    try:
        custom_user = CustomUser.objects.get(id=custom_user_id)
    except CustomUser.DoesNotExist:
        return redirect('login')  # Redirect if the user doesn't exist

    # Check for unanswered feedback questions for the logged-in user
    feedback_questions = FeedbackQuestion.objects.all()
    answered_questions = Feedback.objects.filter(user=custom_user_id).values_list('question_id', flat=True)
    
    # Identify new feedback questions (not answered by the user)
    new_feedback_questions = feedback_questions.exclude(id__in=answered_questions)
    print('New Feedback Questions:', list(new_feedback_questions))

    # Pass the CustomUser object and feedback status to the template
    return render(request, 'student_dashboard.html', {
        'custom_user': custom_user,
        'new_feedback_questions': new_feedback_questions,  # This will contain unanswered questions
    })

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
from django.core.mail import send_mail
from django.contrib import messages
from .models import Teacher, TeacherInterview  # Import the Interview model

def interview_teacher(request):
    # Fetch only teachers with status "pending"
    teachers = Teacher.objects.filter(status='pending')

    if request.method == 'POST':
        # Get form data
        teacher_id = request.POST.get('teacher_id')
        interview_date = request.POST.get('interview_date')
        starting_time = request.POST.get('starting_time')
        ending_time = request.POST.get('ending_time')
        meeting_link = request.POST.get('meeting_link')
        interviewer_name = request.POST.get('interviewer_name')
        notes = request.POST.get('notes')

        # Fetch the teacher based on teacher_id
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            first_name = teacher.first_name
            last_name = teacher.last_name
            teacher_email = teacher.email  # Retrieve teacher's email
        except Teacher.DoesNotExist:
            messages.error(request, 'Teacher not found!')
            return redirect('interview_teacher')

        # Store interview details in the database
        interview = TeacherInterview.objects.create(
            teacher=teacher,
            interview_date=interview_date,
            starting_time=starting_time,
            ending_time=ending_time,
            meeting_link=meeting_link,
            interviewer_name=interviewer_name,
            notes=notes
        )

        # Email content
        subject = "Interview Scheduled for Teacher"
        message = f"""
        Dear {first_name} {last_name},

        You are scheduled for an interview.

        Interview Details:
        Date: {interview_date}
        Starting Time: {starting_time}
        Ending Time: {ending_time}
        Meeting Link: {meeting_link}

        Interviewer: {interviewer_name}
        Notes: {notes}

        Please make sure to attend the meeting on time.

        Best regards,
        {interviewer_name}
        """

        # Sending the email
        send_mail(
            subject,
            message,
            'divyaantony2025@mca.ajce.in',  # From email (replace with your configuration)
            [teacher_email],  # Recipient email
            fail_silently=False,
        )

        messages.success(request, f'Interview scheduled successfully, and email sent to {teacher_email}!')
        return redirect('interview_teacher')

    return render(request, 'interview_teacher.html', {'teachers': teachers})



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
from datetime import date, datetime, time

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
        selected_date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        meeting_link = request.POST.get('meeting_link')

        # Convert strings to appropriate date and time objects
        print("POST data:", request.POST)
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            error_message = "Invalid date or time format. Please use the correct format."
            return render(request, 'schedule_class.html', {
                'courses': courses,
                'today': today,
                'error_message': error_message
            })

        # Validate that the selected date is not in the past
        if selected_date < today:
            error_message = "The selected date cannot be in the past."
            return render(request, 'schedule_class.html', {
                'courses': courses,
                'today': today,
                'error_message': error_message
            })

        # Check that the end time is after the start time
        if end_time <= start_time:
            error_message = "End time must be after the start time."
            return render(request, 'schedule_class.html', {
                'courses': courses,
                'today': today,
                'error_message': error_message
            })

        # Get the selected course object
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            error_message = "Selected course does not exist."
            return render(request, 'schedule_class.html', {
                'courses': courses,
                'today': today,
                'error_message': error_message
            })
        # Create the class schedule record in the database
        schedule = ClassSchedule(
            class_name=class_name,
            course_name=course,
            date=selected_date,
            start_time=start_time,
            end_time=end_time,
            meeting_link=meeting_link,
            teacher=teacher  
        )
        schedule.save()
        if schedule:
            return redirect('teacher_dashboard')  

    current_datetime = datetime.now()
    scheduled_classes = ClassSchedule.objects.filter(teacher=teacher, date__gte=today, end_time__gt=current_datetime.time())

    return render(request, 'schedule_class.html', {
        'courses': courses,
        'today': today,
        'scheduled_classes': scheduled_classes,
        'error_message': error_message
    })

    

from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Q
from .models import ClassSchedule, Teacher, Course

def view_teacher_schedule_class(request):
    # Get the teacher_id from session
    teacher_id = request.session.get('teacher_id')

    # Redirect to login if teacher_id is not present
    if not teacher_id:
        return redirect('login')

    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return redirect('login')

    # Get the current local time and date, automatically converted to IST if TIME_ZONE is set to 'Asia/Kolkata'
    current_datetime = timezone.localtime()

    # Debug statement to check the current IST date and time
    print(f"Current date and time (IST): {current_datetime}")
    print(f"Current date (IST): {current_datetime.date()}, Current time (IST): {current_datetime.time()}")

    # Fetch ongoing and future classes based on the current IST date and time
    future_classes = ClassSchedule.objects.filter(
        teacher=teacher  # Filter classes by teacher
    ).filter(
        Q(date=current_datetime.date(), end_time__gt=current_datetime.time()) |  # Ongoing classes today that haven't ended
        Q(date__gt=current_datetime.date())  # Future classes (scheduled after today)
    ).order_by('date', 'start_time')  # Order by date and start time

    # Debug statement to check the ongoing and future classes query results
    print(f"Ongoing and future classes: {future_classes}")

    # Prepare the context for rendering
    context = {
        'future_classes': future_classes,  # Ongoing and future classes
    }

    return render(request, 'view_teacher_schedule_class.html', context)



from django.shortcuts import render, redirect # type: ignore
from django.contrib import messages # type: ignore
from .models import ClassSchedule

def edit_class(request):
    courses = Course.objects.all()
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        course_id = request.POST.get('course_name')
        class_name = request.POST.get('class_name')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        meeting_link = request.POST.get('meeting_link')

        try:
            scheduled_class = ClassSchedule.objects.get(id=class_id)
            scheduled_class.course_name = course_id
            scheduled_class.class_name = class_name
            scheduled_class.date = date
            scheduled_class.start_time = start_time
            scheduled_class.end_time = end_time
            scheduled_class.meeting_link = meeting_link
            scheduled_class.save()

            messages.success(request, "Class details updated successfully.")
        except ClassSchedule.DoesNotExist:
            messages.error(request, "Class not found.")

        return redirect('view_teacher_schedule_class', {'courses': courses})  # Redirect to the view scheduled classes page

from django.contrib import messages # type: ignore
from django.shortcuts import redirect, render # type: ignore
from .models import ClassSchedule, CustomUser
from django.utils import timezone # type: ignore
from django.db.models import Q # type: ignore

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
    registered_course = student.course_id
    if not registered_course:
        messages.error(request, "You are not registered for any course.")
        return redirect('student_dashboard')

    # Get the current date and time in IST
    current_datetime = timezone.localtime()  # This will automatically convert to IST if TIME_ZONE is set to 'Asia/Kolkata'

    # Debug statement to check the current IST date and time
    print(f"Current date and time (IST): {current_datetime}")

    # Fetch ongoing and future classes for the registered course
    ongoing_future_classes = ClassSchedule.objects.filter(
        course_name=registered_course  # Filter classes based on the student's registered course
    ).filter( 
        Q(date=current_datetime.date(), end_time__gt=current_datetime.time()) |  # Ongoing classes today that haven't ended
        Q(date__gt=current_datetime.date())  # Future classes (after today)
    ).order_by('date', 'start_time')  # Order by date and start time

    # Check if there are any ongoing or future classes
    if not ongoing_future_classes.exists():
        messages.info(request, "No ongoing or upcoming classes found.")

    # Pass the classes to the template
    return render(request, 'view_scheduled_classes.html', {'scheduled_classes': ongoing_future_classes})


from django.shortcuts import render, redirect # type: ignore
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


from .models import CustomUser, Parent, Teacher
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


from django.shortcuts import render, redirect # type: ignore
from django.contrib import messages # type: ignore
from django.contrib.auth import update_session_auth_hash # type: ignore
from .models import CustomUser, Parent, Teacher
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



from .models import Teacher

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


from .models import Parent

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

from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
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
from .models import Material, Parent, CustomUser

def view_study_materials(request):

    parent = get_object_or_404(Parent, auto_generated_username=request.user.username)
    
    student = get_object_or_404(CustomUser, username=parent.student_username)

    materials = Material.objects.filter(course=student.course)
    
    return render(request, 'view_study_materials.html', {'materials': materials, 'student': student})

from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.utils import timezone # type: ignore
from .models import Quizs, Question, Course, Teacher


def create_quiz(request):
    if request.method == 'POST':
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        course = get_object_or_404(Course, id=course_id)
        teacher_id = request.session.get('teacher_id')  # Retrieve the teacher's ID from the session

        if not teacher_id:
            # Handle the case where the teacher is not logged in
            return redirect('login')

        quiz = Quizs(course=course, teacher_id=teacher_id, title=title, start_date=start_date,
                     end_date=end_date, start_time=start_time, end_time=end_time)
        quiz.save()

        return redirect('add_question', quiz_id=quiz.id)
    
    courses = Course.objects.all()
    return render(request, 'create_quiz.html', {'courses': courses})

def add_question(request, quiz_id):
    quiz = get_object_or_404(Quizs, id=quiz_id)

    if request.method == 'POST':
        questions_data = request.POST.getlist('question')
        options_a = request.POST.getlist('option_a')
        options_b = request.POST.getlist('option_b')
        options_c = request.POST.getlist('option_c')
        options_d = request.POST.getlist('option_d')
        correct_options = request.POST.getlist('correct_option')

        # Iterate through all submitted questions
        for i in range(len(questions_data)):
            question_text = questions_data[i]
            option_a = options_a[i]
            option_b = options_b[i]
            option_c = options_c[i]
            option_d = options_d[i]
            correct_option = correct_options[i]

            # Create a new Question object for each set of data
            question = Question(
                quiz=quiz, 
                text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_option=correct_option
            )
            question.save()

        return redirect('add_question', quiz_id=quiz.id)

    return render(request, 'add_question.html', {'quiz': quiz})


from django.shortcuts import render, get_object_or_404
from .models import Quizs, Question

def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quizs, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz)

    if request.method == 'POST':
        user_answers = {}  # Store user's answers
        correct_count = 0  # Track the number of correct answers

        # Loop through each question in the quiz
        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}')  # Get user's answer for the question
            user_answers[question.id] = user_answer  # Save the user's answer

            # Check if the user's answer matches the correct answer
            if user_answer == question.correct_option:
                correct_count += 1  # Increment correct count if answer is correct

        # After submission, show the result
        return render(request, 'quiz_result.html', {
            'quiz': quiz,
            'questions': questions,
            'user_answers': user_answers,
            'correct_count': correct_count,
            'total_questions': questions.count()
        })

    # Render the quiz page with questions
    return render(request, 'take_quiz.html', {
        'quiz': quiz,
        'questions': questions
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import CustomUser, Quizs  # Adjust based on your app's structure

def available_quizzes(request):
    # Retrieve the custom user ID from the session
    custom_user_id = request.session.get('custom_user_id')

    if not custom_user_id:
        messages.error(request, "You are not logged in.")
        return redirect('login')  # Redirect to login page if user ID is not in session

    try:
        # Fetch the student (CustomUser) based on the custom user ID
        student = CustomUser.objects.get(id=custom_user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('login')

    # Check the registered course for the student
    registered_course = student.course  # Assuming there's a course field on CustomUser

    if not registered_course:
        messages.error(request, "You are not registered for any course.")
        return redirect('student_dashboard')

    # Get current time in IST (based on TIME_ZONE setting in settings.py)
    current_datetime = timezone.localtime()

    # Debug statement to check the current IST date and time
    print(f"Current date and time (IST): {current_datetime}")

    # Fetch quizzes related to the registered course that are ongoing or in the future
    quizzes = Quizs.objects.filter(
        course=registered_course
    ).filter(
        Q(start_date=current_datetime.date(), end_time__gt=current_datetime.time(), end_date=current_datetime.date()) |  # Ongoing quizzes today
        Q(start_date=current_datetime.date(), end_date__gt=current_datetime.date()) |  # Future quizzes (after today)
        Q(start_date__gt=current_datetime.date())  # Future quizzes (after today)
    ).order_by('start_date', 'start_time')  # Optional: order quizzes by start date and time

    # Render the available quizzes template
    return render(request, 'available_quizzes.html', {'quizzes': quizzes})


def submit_quiz(request, quiz_id):
    # Get the quiz and its associated questions
    quiz = get_object_or_404(Quizs, id=quiz_id)
    questions = quiz.questions.all()

    # Retrieve the `custom_user_id` from the session
    custom_user_id = request.session.get('custom_user_id')
    if not custom_user_id:
        messages.error(request, "You must be logged in to submit the quiz.")
        return redirect('login')

    # Fetch the CustomUser based on the custom user ID from the session
    try:
        custom_user = CustomUser.objects.get(id=custom_user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    # Initialize counters
    correct_count = 0
    total_questions = questions.count()

    # Prepare to store user answers with questions
    question_data = []

    # Loop through the quiz questions
    for question in questions:
        # Get the user's selected answer from POST data
        user_answer = request.POST.get(f'question_{question.id}')

        # Only process if the user provided an answer
        if user_answer in ['A', 'B', 'C', 'D']:
            # Store the user's answer in the UserAnswers table
            UserAnswers.objects.update_or_create(
                user=custom_user,
                question=question,
                defaults={'selected_option': user_answer}
            )

            # Increment correct count if the answer is correct
            if user_answer == question.correct_option:
                correct_count += 1
        else:
            user_answer = None

        # Retrieve the stored answer from the database
        try:
            stored_answer = UserAnswers.objects.get(user=custom_user, question=question).selected_option
        except UserAnswers.DoesNotExist:
            stored_answer = "Not answered"

        # Append the question and user answer to the list
        question_data.append({
            'question': question,
            'user_answer': stored_answer,
            'correct_answer': question.correct_option,
        })

    # Render the result page, passing the structured data to the template
    context = {
        'quiz': quiz,
        'questions_data': question_data,
        'correct_count': correct_count,
        'total_questions': total_questions,
    }
    return render(request, 'quiz_result.html', context)


def quiz_result(request, quiz_id):
    # Ensure the user is logged in
    custom_user_id = request.session.get('custom_user_id')
    if not custom_user_id:
        messages.error(request, "You must be logged in to view quiz results.")
        return redirect('login')

    # Get the quiz
    quiz = get_object_or_404(Quizs, id=quiz_id)

    # Retrieve user's answers for the specific quiz
    user_answers = UserAnswers.objects.filter(user_id=custom_user_id, question__quiz=quiz)

    # Prepare data for display
    results = []
    correct_count = 0
    total_questions = quiz.questions.count()

    # Create a dictionary to map question ids to user answers
    user_answers_dict = {user_answer.question.id: user_answer.selected_option for user_answer in user_answers}

    for question in quiz.questions.all():  # Iterate through all questions in the quiz
        selected_option = user_answers_dict.get(question.id, "Not answered")  # Get the selected option or default to "Not answered"
        correct_answer = question.correct_option
        is_correct = (selected_option == correct_answer)

        results.append({
            'question': question,
            'selected_option': selected_option,
            'correct_option': correct_answer,
            'is_correct': is_correct,  # Keep track of whether the answer is correct
        })

        if is_correct:
            correct_count += 1

    context = {
        'quiz': quiz,
        'results': results,
        'correct_count': correct_count,
        'total_questions': total_questions,
    }
    return render(request, 'quiz_result.html', context)


def quiz_questions(request, quiz_id):
    quiz = Quizs.objects.get(id=quiz_id)
    questions = Question.objects.filter(quizs=quiz)  # Adjust based on your models

    return render(request, 'quiz_questions.html', {'quiz': quiz, 'questions': questions})

from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.http import HttpResponse # type: ignore
from .models import Assignment, Course, Teacher
from django.core.exceptions import ValidationError # type: ignore
from datetime import datetime

def create_assignment(request):
    if request.method == 'POST':
        # Fetch form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        course_name_id = request.POST.get('course')
        file = request.FILES.get('file')

        # Validate and convert date and time
        try:
            # Convert start_date and end_date from string to date
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Convert start_time and end_time from string to time
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()

            # Get the teacher from the session
            teacher_id = request.session.get('teacher_id')
            teacher_id = request.session.get('teacher_id')
            if teacher_id:
                teacher = get_object_or_404(Teacher, id=teacher_id)

            # Create the assignment instance
            assignment = Assignment(
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                file=file,
                course_name_id=course_name_id,
                teacher=teacher  # Use the logged-in teacher from session
            )

            # Custom validation checks
            if assignment.start_date > assignment.end_date:
                raise ValidationError("Start date cannot be after end date.")

            # Save the assignment to the database
            assignment.save()

            # Redirect to teacher dashboard on success
            return redirect('teacher_dashboard')  # Update this to your actual dashboard URL name

        except ValidationError as e:
            # Render the create assignment page with the error message
            return render(request, 'create_assignment.html', {
                'error': str(e),
                'courses': Course.objects.all(),
                'assignment': request.POST  # Preserving the submitted data
            })
        except Exception as e:
            # Handle other exceptions and render the same page
            return render(request, 'create_assignment.html', {
                'error': "An error occurred. Please try again.",
                'courses': Course.objects.all(),
                'assignment': request.POST  # Preserving the submitted data
            })

    else:
        # Fetch the list of courses to display in the form
        courses = Course.objects.all()
        return render(request, 'create_assignment.html', {'courses': courses})


from django.contrib import messages  # type: ignore
from django.shortcuts import redirect, render  # type: ignore
from django.utils import timezone # type: ignore
from .models import Assignment, AssignmentSubmission, CustomUser  # Ensure to import your models

def assignment_submission_view(request):
    # Retrieve the custom user ID from the session
    custom_user_id = request.session.get('custom_user_id')

    if not custom_user_id:
        messages.error(request, "You are not logged in.")
        return redirect('login')  # Redirect to login page if user ID is not in session

    try:
        # Fetch the student (CustomUser) based on the custom user ID
        student = CustomUser.objects.get(id=custom_user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('login')

    # Check the registered course for the student
    registered_course = student.course  # Assuming there's a course_id field on CustomUser
    if not registered_course:
        messages.error(request, "You are not registered for any course.")
        return redirect('student_dashboard')

    # Fetch assignments based on the registered course only
    assignments = Assignment.objects.filter(course_name=registered_course)

    # Create a list to store assignment details with submission status
    assignment_details = []

    for assignment in assignments:
       current_datetime = timezone.now()
       assignment_end_datetime = datetime.combine(assignment.end_date, assignment.end_time)

       assignment_end_datetime = timezone.make_aware(assignment_end_datetime)


       has_reached_deadline = assignment_end_datetime <= current_datetime
    
       # Check if the student has submitted the assignment
       submission = AssignmentSubmission.objects.filter(assignment=assignment, student=student).first()
        # Build the details for each assignment
       assignment_detail = {
            'assignment': assignment,
            'submission': submission,
            'has_reached_deadline': has_reached_deadline,
            'can_submit': not has_reached_deadline and not submission,
            'submission_allowed': not has_reached_deadline and submission,  # Option to re-submit before the deadline
        }
       assignment_details.append(assignment_detail)

    # Handle the file upload if the request method is POST
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id')  # Get the assignment ID from the form
        file = request.FILES.get('file')
        if file and assignment_id:
            # Fetch the specific assignment based on the assignment ID
            assignment = Assignment.objects.filter(id=assignment_id, course_name=registered_course).first()
            
            if assignment and not has_reached_deadline and not submission:
                # Create a new submission
                submission = AssignmentSubmission(
                    assignment=assignment,
                    student=student,
                    file=file
                )
                submission.save()
                messages.success(request, 'Your submission has been uploaded successfully!')
                return redirect('student_dashboard')  # Redirect to your desired page
            else:
                if has_reached_deadline:
                    messages.error(request, "Assignment deadline has passed, submission not allowed.")
                else:
                    messages.error(request, "Assignment already submitted.")
        else:
            messages.error(request, 'Please upload a file and select an assignment.')

    # Render the assignment details template with the list of assignment details
    return render(request, 'assignment_detail.html', {'assignment_details': assignment_details})


from django.shortcuts import render, redirect  # type: ignore
from django.utils import timezone
from .models import Assignment, Course

def view_assignment(request):
    if 'teacher_id' in request.session:
        teacher_id = request.session['teacher_id']

        # Fetch all courses from the Course table
        courses = Course.objects.all()

        # Get the selected course ID from the GET request
        selected_course_id = request.GET.get('course_id')

        # Fetch assignments for the selected course or all assignments if no course is selected
        if selected_course_id:
            assignments = Assignment.objects.filter(course_name__id=selected_course_id, teacher_id=teacher_id)
        else:
            assignments = Assignment.objects.filter(teacher_id=teacher_id)

        # Get the current date and time
        current_datetime = timezone.localtime()

        # Add a 'status' attribute to each assignment based on end date and time
        for assignment in assignments:
            if (assignment.end_date < current_datetime.date() or
                (assignment.end_date == current_datetime.date() and assignment.end_time <= current_datetime.time())):
                assignment.status = 'Completed'
            else:
                assignment.status = 'Ongoing'

        return render(request, 'view_assignment.html', {
            'assignments': assignments,
            'courses': courses,
            'selected_course_id': selected_course_id,
        })
    else:
        return redirect('login')



from django.db.models import Subquery, OuterRef # type: ignore
from django.shortcuts import render # type: ignore
from .models import AssignmentSubmission, Course

def evaluate_assignments(request):
    selected_course_id = request.GET.get('course_id')
    courses = Course.objects.all()

    # Get the latest submission for each student
    latest_submissions = AssignmentSubmission.objects.filter(
        student=OuterRef('student'),
        assignment=OuterRef('assignment')
    ).order_by('-submitted_at')

    if selected_course_id:
        # Filter by course and ensure we only get the latest submission for each student
        submissions = AssignmentSubmission.objects.filter(
            assignment__course_name__id=selected_course_id,
            submitted_at=Subquery(latest_submissions.values('submitted_at')[:1])
        )
    else:
        # Get the latest submission for each student across all courses
        submissions = AssignmentSubmission.objects.filter(
            submitted_at=Subquery(latest_submissions.values('submitted_at')[:1])
        )

    context = {
        'submissions': submissions,
        'courses': courses,
        'selected_course_id': selected_course_id,
    }
    return render(request, 'evaluate_assignment.html', context)

from django.shortcuts import get_object_or_404, redirect # type: ignore
from .models import AssignmentSubmission
from django.views.decorators.http import require_POST # type: ignore


@require_POST # type: ignore
def submit_grade(request, submission_id):
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    grade = request.POST.get('grade')

    if grade is not None:
        submission.grade = grade  # Store the grade in the grade field
        submission.save()  # Save the submission to update the database

    return redirect('evaluate_assignment')

from django.shortcuts import render, redirect
from .models import FeedbackQuestion

def add_feedback_question(request):
    if request.method == 'POST':
        questions = []
        for key, value in request.POST.items():
            if key.startswith('question_text_'):
                questions.append(value)

        if questions:
            for question_text in questions:
                FeedbackQuestion.objects.create(question_text=question_text)  # Save each question to the database
            return redirect('admin_dashboard')  # Redirect to admin dashboard after saving
        else:
            return render(request, 'add_feedback_question.html', {'error': 'Please enter at least one question.'})

    return render(request, 'add_feedback_question.html')


from django.shortcuts import render, redirect
from .models import Feedback, FeedbackQuestion

def feedback_view(request):
    user_id = request.session.get('custom_user_id', 'Anonymous')  # Get the user ID from the session

    # Get a list of questions that the user has already answered
    answered_questions = Feedback.objects.filter(user=user_id).values_list('question_id', flat=True)

    # Load only the questions that the user has not yet answered
    questions = FeedbackQuestion.objects.exclude(id__in=answered_questions)

    if request.method == 'POST':
        for question in questions:
            response = request.POST.get(f'question_{question.id}')
            if response:  # Ensure there's a response before saving
                Feedback.objects.create(
                    user=user_id,
                    question=question,
                    response=response
                )
        return redirect('student_dashboard')  # Redirect to a thank you page or another view

    return render(request, 'feedback_form.html', {'questions': questions})

def thank_you_view(request):
    return render(request, 'thank_you.html')

from django.shortcuts import render
from .models import Feedback

def view_feedback_responses(request):
    feedback_responses = Feedback.objects.all()  # Fetch all feedback responses
    return render(request, 'view_feedback_responses.html', {'feedback_responses': feedback_responses})


# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import CalendarEvent, Course

def add_event(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        description = request.POST.get('description', '')
        event_type = request.POST.get('event_type')
        course_id = request.POST.get('course_id')

        # Debugging: print the received values
        print(f'Title: {title}, Start Time: {start_time}, End Time: {end_time}, Course ID: {course_id}')
        
        # Check if course_id is provided
        if not course_id:
            courses = Course.objects.all()  # Fetch courses to repopulate the form
            return render(request, 'add_event.html', {'error': 'Course must be selected.', 'courses': courses})

        # Convert start_time and end_time
        start_time = timezone.make_aware(timezone.datetime.fromisoformat(start_time))
        end_time = timezone.make_aware(timezone.datetime.fromisoformat(end_time))

        # Create the CalendarEvent object
        event = CalendarEvent(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            event_type=event_type,
            course_id=course_id,
            created_by_id=request.session.get('teacher_id')  # Set created_by to the teacher
        )
        
        # Attempt to save the event
        try:
            event.save()
            print('Event saved successfully!')
        except Exception as e:
            print(f'Error saving event: {e}')
        
        return redirect('view_events')  # Redirect to the event list after saving

    courses = Course.objects.all()  # Fetch courses for the dropdown
    return render(request, 'add_event.html', {'courses': courses})  # Render the template with courses


from django.shortcuts import render
from .models import Course, CalendarEvent  # Import your models

def view_events(request):
    teacher_id = request.session.get('teacher_id')
    
    # Fetch events created by the teacher
    events = CalendarEvent.objects.filter(created_by_id=teacher_id)

    # Fetch all courses (or you can filter based on the teacher's courses if applicable)
    courses = Course.objects.all()  # Adjust this line if you need specific courses for the teacher

    return render(request, 'view_events.html', {
        'events': events,
        'courses': courses  # Pass courses to the template
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import CalendarEvent
from django.contrib.auth import get_user_model

def student_events(request):
    CustomUser = get_user_model()  # Fetch the custom user model
    custom_user_id = request.session.get('custom_user_id')

    if not custom_user_id:
        messages.error(request, 'You must be logged in as a student to view events.')
        return redirect('login')  # Redirect to login if no user session

    # Fetch the CustomUser (student) object using the session ID
    student = get_object_or_404(CustomUser, id=custom_user_id)

    # Fetch the course associated with the student
    course = student.course  # This will fetch the course if exists

    if not course:
        messages.error(request, 'You are not registered for any courses.')
        return redirect('student_dashboard')  # Redirect if no course is associated

    # Fetch events for the course the student is enrolled in
    events = CalendarEvent.objects.filter(course=course)
    event_type = request.GET.get('event_type', '')
    if event_type:
        events = events.filter(event_type=event_type)  # Filter by event type
    context = {
        'events': events,
        'courses': course,
    }    

    return render(request, 'student_event.html', context)


from django.http import JsonResponse
from .models import CalendarEvent

def filtered_events(request):
    event_type = request.GET.get('event_type', '')
    course_id = request.GET.get('course_id', '')
    events = CalendarEvent.objects.all()

    if event_type:
        events = events.filter(event_type=event_type)
    if course_id:
        events = events.filter(course_id=course_id)    

    event_list = [{
        'title': event.title,
        'start': event.start_time.isoformat(),
        'end': event.end_time.isoformat(),
        'description': event.description,
        'event_type': event.event_type,
        'color': get_event_color(event.event_type),
    } for event in events]

    return JsonResponse(event_list, safe=False)

def get_event_color(event_type):
    color_map = {
        'class': '#ffcc00',  # Yellow for classes
        'assignment': '#00ccff',      # Blue for assignments
        'exam': '#ff6666',            # Red for exams
        'holiday': '#28a745',         # Green for holidays
        'personal_event': '#6c757d'   # Gray for personal events
    }
    return color_map.get(event_type, '#007bff')  # Default to Bootstrap primary color



from django.shortcuts import render, redirect
from .models import Quizs, Course, Question

def view_quiz_questions(request):
    teacher_id = request.session.get('teacher_id')  # Retrieve the teacher_id from the session

    if not teacher_id:
        # If the teacher is not logged in or the session has expired, redirect to the login page
        return redirect('login')

    course_id = request.GET.get('course_id')  # Get the course ID from the query parameters
    courses = Course.objects.all()  # Get all available courses for the filter dropdown

    # Fetch quizzes created by this teacher
    quizzes = Quizs.objects.filter(teacher_id=teacher_id)
    
    # Fetch questions for quizzes of the selected course
    questions = Question.objects.none()  # Start with an empty QuerySet

    if course_id:  # If a course is selected, filter questions by that course
        # Filter quizzes based on the course and fetch related questions
        quizzes = quizzes.filter(course_id=course_id)
        questions = Question.objects.filter(quiz__in=quizzes)  # Fetch questions for the selected course's quizzes

    context = {
        'courses': courses,
        'questions': questions,
        'selected_course': course_id,
    }
    return render(request, 'view_quiz_questions.html', context)


from django.shortcuts import render, redirect
from .models import Question, UserAnswers, Quizs

def view_student_answers(request):
    teacher_id = request.session.get('teacher_id')  # Retrieve the teacher_id from the session

    if not teacher_id:
        return redirect('login')

    # Fetch all quizzes related to the teacher
    quizzes = Quizs.objects.filter(teacher_id=teacher_id)  # Adjust this if needed

    # Fetch all questions related to those quizzes
    questions = Question.objects.filter(quiz__in=quizzes)

    # Fetch all student answers for those questions
    student_answers = UserAnswers.objects.filter(question__in=questions).select_related('user')

    context = {
        'quizzes': quizzes,
        'student_answers': student_answers,
    }

    return render(request, 'view_student_answers.html', context)


from django.shortcuts import render
from .models import Material, Course

def view_uploaded_materials(request):
    # Assuming you have a session variable for the logged-in teacher
    teacher_id = request.session.get('teacher_id')
    
    # Fetch courses taught by the teacher
    courses = Course.objects.all() 
    course_id = request.GET.get('course', None)  # Get the selected course from the dropdown filter
    materials = Material.objects.filter(teacher_id=teacher_id)  # Get materials uploaded by the teacher

    # Filter materials by the selected course if course_id is provided
    if course_id:
        materials = materials.filter(course_id=course_id)

    context = {
        'materials': materials,
        'courses': courses,
        'selected_course': course_id,
    }
    return render(request, 'view_uploaded_materials.html', context)
