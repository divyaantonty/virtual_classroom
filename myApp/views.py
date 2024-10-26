import json
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
import requests
from .models import CustomUser, Course, Parent, TeacherMessage

def register(request):
    if request.method == 'POST':
        # Extract form data from request.POST
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        date_of_birth = request.POST.get('date_of_birth')
        username = request.POST.get('username')
        password = request.POST.get('password')
       

        # Perform basic validation
        if not all([first_name, last_name, email, contact, date_of_birth, username, password]):
            messages.error(request, 'Please fill out all fields.')
            return render(request, 'register.html')

        if not username.isalnum():
            messages.error(request, "Username should contain only alphabets or numbers.")
            return redirect('register')

        # Check if the username or email is unique for the student
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
            return render(request, 'register.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return render(request, 'register.html')

        # Validate email format
        
        # Validate password complexity
       


        # Create and save student user instance
        student_user = CustomUser(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            contact=contact,
            date_of_birth=date_of_birth,
            password=make_password(password),
            is_active=True,  # Ensure the user is active upon registration
        )
        student_user.save()

        # Auto-generate a unique parent username using UUID
        parent_username = f'parent_{uuid.uuid4().hex[:8]}'  # Generate an 8-character unique username

        # Generate a random secure password for the parent
        parent_password = get_random_string(12)  # Generate a 12-character password

        # Create the parent instance linked to the student user
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
        return render(request, 'register.html')



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
            if not custom_user.is_active:
                messages.error(request, 'Your account is deactivated. Please contact support.')
            if custom_user.check_password(password):  # Assuming password is stored as plaintext
                # Manually log in the CustomUser (using sessions)
                request.session['custom_user_id'] = custom_user.id  # Store CustomUser ID in session
                return redirect('available_courses')
            else:
                messages.error(request, 'Invalid password for CustomUser.')
        except CustomUser.DoesNotExist:
            pass  # Not a CustomUser

        # If no match, show an error message
        messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')

def assigned_courses(request):
    # Get the teacher ID from the session
    teacher_id = request.session.get('teacher_id')

    if teacher_id:
        # Fetch the assigned courses from the session
        assigned_courses = request.session.get('assigned_courses', [])

        return render(request, 'assigned_courses.html', {'courses': assigned_courses})

    return redirect('teacher_login')  # Redirect to login if no session found


from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Course, Enrollment

def available_courses(request):
    # Check if the user is authenticated via session
    if 'custom_user_id' not in request.session:
        return redirect('login')  # Redirect to the login page if not authenticated

    # Get the logged-in user's ID from the session
    custom_user_id = request.session['custom_user_id']

    courses = Course.objects.all()

    current_date = timezone.now().date()

    price_range = request.GET.get('price_range')
    if price_range:
        if price_range == 'all':
            pass
        elif price_range == '0-500':
            courses = courses.filter(price__lt=500)
        elif price_range == '1000-2000':
            courses = courses.filter(price__gte=1000, price__lt=2000)
        elif price_range == '2000-3000':
            courses = courses.filter(price__gte=2000, price__lt=3000)
        elif price_range == '3000-4000':
            courses = courses.filter(price__gte=3000, price__lt=4000)
        elif price_range == '4000-5000':
            courses = courses.filter(price__gte=4000, price__lt=5000)
        elif price_range == '5000+':
            courses = courses.filter(price__gte=5000)

    # Get the current date
  

    # Prepare a list to hold course data along with enrollment status
    course_data = []

    for course in courses:
        # Check if the user is enrolled in the current course
        is_enrolled = Enrollment.objects.filter(student_id=custom_user_id, course=course).exists()
        
        # Append course data with the enrollment status and start date check
        course_data.append({
            'course': course,
            'is_enrolled': is_enrolled,
            'can_enroll': current_date < course.starting_date  # Check if course hasn't started yet
        })

    # Pass the course data and current date to the template
    return render(request, 'available_courses.html', {
        'custom_user': custom_user_id,
        'course_data': course_data,
        'current_date': current_date,
        'selected_price_range':price_range
    })

from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Enrollment
from django.http import HttpResponseForbidden

def enroll_course(request, course_id):
    # Check if the user is authenticated via session
    if 'custom_user_id' not in request.session:
        # If the user is not authenticated, redirect to the login page
        return redirect('login')  # Redirect to your custom login page

    # Get the authenticated user's ID from the session
    custom_user_id = request.session['custom_user_id']
    
    # Get the course the user is trying to enroll in
    course = get_object_or_404(Course, id=course_id)

    # Check if the user is already enrolled in this course
    if Enrollment.objects.filter(student_id=custom_user_id, course=course).exists():
        # You can add a message here indicating the user is already enrolled
        return redirect('available_courses')  # Redirect back to the available courses page

    # If the user is not enrolled, create a new Enrollment
    enrollment = Enrollment.objects.create(student_id=custom_user_id, course=course)

    # Optionally, you can show a success message or redirect to another page
    return redirect('available_courses')  # Redirect to the course list page

from django.shortcuts import render, redirect
from .models import CustomUser, FeedbackQuestion, Feedback

def student_dashboard(request):
    custom_user_id = request.session.get('custom_user_id')
    if not custom_user_id:
        return redirect('login')  # Redirect to login if CustomUser not authenticated

    # Fetch the CustomUser object based on the session ID
    try:
        custom_user = CustomUser.objects.get(id=custom_user_id)
        if not custom_user.is_active:
            return redirect('login')
    except CustomUser.DoesNotExist:
        return redirect('login')  # Redirect if the user doesn't exist
    enrolled_courses = Course.objects.filter(enrollments__student_id=custom_user_id)
    # Check for unanswered feedback questions for the logged-in user
    feedback_questions = FeedbackQuestion.objects.all()
    answered_questions = Feedback.objects.filter(user=custom_user_id).values_list('question_id', flat=True)
    
    # Identify new feedback questions (not answered by the user)
    new_feedback_questions = feedback_questions.exclude(id__in=answered_questions)
    print('New Feedback Questions:', list(new_feedback_questions))

    # Pass the CustomUser object and feedback status to the template
    return render(request, 'student_dashboard.html', {
        'enrolled_courses': enrolled_courses,
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
    teacher_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).select_related('course')
    # Pass the teacher object to the template
    return render(request, 'teacher_dashboard.html', {
        'first_name': teacher.first_name,
        'last_name': teacher.last_name,
        'teacher_courses': teacher_courses
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
# views.py
from django.shortcuts import render
from .models import CustomUser, Teacher, Course  # Import your models

def admin_dashboard(request):
    # Count the number of users, teachers, and courses
    total_users = CustomUser.objects.count()
    total_teachers = Teacher.objects.count()
    total_courses = Course.objects.count()

    context = {
        'total_users': total_users,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
    }

    return render(request, 'admin_dashboard.html', context)


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


# views.py
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import CustomUser

def toggle_student_status(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id)
    if student.is_active:
        student.is_active = 0
        email_subject = "Account Deactivated"
        email_message = "Your account has been deactivated. Please contact support if you have any questions."
    else:
        student.is_active = True
        email_subject = "Account Activated"
        email_message = "Your account has been activated. You can now log in to the platform."

    student.save()

    # Send email to the student
    send_mail(
        email_subject,
        email_message,
        'divyaantony2025.mca.ajce.in',
        [student.email],
        fail_silently=False,
    )

    messages.success(request, f"Student '{student.username}' status updated successfully.")
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
from .models import Teacher

def register_teacher(request):
    if request.method == 'POST':
        # Extract data from the POST request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        dob = request.POST.get('dob')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')

        # Handle file uploads
        qualification_certificate = request.FILES.get('qualification_certificate')
        experience_certificate = request.FILES.get('experience_certificate', None)  # This file is optional

        # Simple validation check for required fields
        if not first_name or not last_name or not email:
            messages.error(request, "First name, last name, and email are required.")
        else:
            # Create a new Teacher object and set the fields
            teacher = Teacher(
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=dob,
                email=email,
                contact=contact,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                zip_code=zip_code,
                qualification=qualification,
                experience=experience,
                qualification_certificate=qualification_certificate,
                experience_certificate=experience_certificate,  # This file is optional
                status='pending'  # Set the initial status of the teacher to 'pending'
            )
            teacher.save()

            # Add a success message
            messages.success(request, "You have successfully registered! Please wait for your approval.")

            # Redirect to the login page or another relevant page after successful registration
            return redirect('login')

    return render(request, 'register_teacher.html')



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

# views.py
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Teacher  # Import your Teacher model

def toggle_teacher_status(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    if teacher.is_active:
        teacher.is_active = False  # Set to False to deactivate
        email_subject = "Account Deactivated"
        email_message = "Your account has been deactivated. Please contact support if you have any questions."
    else:
        teacher.is_active = True  # Set to True to activate
        email_subject = "Account Activated"
        email_message = "Your account has been activated. You can now log in to the platform."

    teacher.save()

    # Send email to the teacher
    send_mail(
        email_subject,
        email_message,
        'your_email@example.com',  # Replace with your email
        [teacher.email],  # Send email to the teacher
        fail_silently=False,
    )

    messages.success(request, f"Teacher '{teacher.first_name} {teacher.last_name}' status updated successfully.")
    return redirect('manage_teachers')


from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import Teacher, Course, TeacherCourse  # Assuming TeacherCourse is the model for the relationship
from .forms import ApproveTeacherForm

def approve_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    courses = Course.objects.all()
    
    if request.method == 'POST':
        form = ApproveTeacherForm(request.POST, instance=teacher)
        
        if form.is_valid():
            if teacher.status != 'approved':
                teacher.status = 'approved'
                
                # Process selected courses and teaching areas
                selected_courses = request.POST.getlist('courses')  # This retrieves a list of selected course IDs
                for course_id in selected_courses:
                    course = get_object_or_404(Course, id=course_id)
                    teaching_area = request.POST.get(f'teaching_area_{course_id}', '')  # Get the teaching area for each course
                    
                    # Create or update the TeacherCourse relationship
                    TeacherCourse.objects.create(teacher=teacher, course=course, teaching_area=teaching_area)

                teacher.save()

                # Debugging: Check if teacher is approved
                print(f"Teacher {teacher.first_name} {teacher.last_name} is now approved")
             
                # Generate random username and password
                random_username = f"teacher_{get_random_string(8)}"  
                random_password = get_random_string(8)  

                # Debugging: Check if credentials are generated
                print(f"Generated credentials: {random_username}, {random_password}")
                
                teacher.auto_generated_username = random_username
                teacher.auto_generated_password = random_password  
                teacher.save()

                # Send email to the teacher
                subject = 'Your Teacher Account has been Approved'
                message = (
                    f"Dear {teacher.first_name} {teacher.last_name},\n\n"
                    f"Your account has been approved! Here are your login details:\n\n"
                    f"Username: {random_username}\n"
                    f"Password: {random_password}\n\n"
                    f"You have been assigned to teach the course(s).\n"
                    f"Teaching Area: **{teaching_area}**.\n\n"
                    "Please log in and change your password upon your first login.\n\n"
                    "Best Regards,\n"
                    "The Administration Team"
                )

                # Send the email
                send_mail(
                    subject,
                    message,
                    'divyaantony2025@mca.ajce.in',  
                    [teacher.email],
                    fail_silently=False,
                )

                return redirect('admin_dashboard')  
            else:
                print("Teacher is already approved")
        else:
            print(form.errors)

    else:
        form = ApproveTeacherForm(instance=teacher)

    context = {
        'form': form,
        'teacher': teacher,
        'courses': courses,
    }

    return render(request, 'approve_teacher.html', context)


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
        return redirect('admin_dashboard')

    return render(request, 'interview_teacher.html', {'teachers': teachers})



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Course

def add_course(request):
    if request.method == 'POST':
        course_name = request.POST.get('course_name')
        description = request.POST.get('description')
        duration = request.POST.get('duration')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        start_date = request.POST.get('start_date')  # getting the start date
        end_date = request.POST.get('end_date')

        new_course = Course(course_name=course_name, description=description, duration=int(duration), price=price, image=image,starting_date=start_date,  # saving start date
            ending_date=end_date,)
        new_course.save()

        messages.success(request, 'Course added successfully!')
        return redirect('course_list')
    else:
        return render(request, 'add_courses.html')



def course_list(request):
    courses = Course.objects.all()  
    return render(request, 'course_list.html', {'courses': courses})

from django.shortcuts import render, redirect
from .models import Course, ClassSchedule, Teacher, TeacherCourse
from datetime import date, datetime

def schedule_class(request):
    teacher_id = request.session.get('teacher_id')  # Get teacher ID from session
    if not teacher_id:
        return redirect('login')  # Redirect to login if teacher ID is missing
    
    try:
        teacher = Teacher.objects.get(id=teacher_id)  # Fetch the logged-in teacher
    except Teacher.DoesNotExist:
        return redirect('login')  # Redirect to login if teacher is not found

    # Fetch the assigned courses from TeacherCourse model
    assigned_courses = TeacherCourse.objects.filter(teacher=teacher)
    
    if not assigned_courses.exists():
        error_message = "No course is assigned to you."
        return render(request, 'schedule_class.html', {
            'today': date.today(),
            'error_message': error_message
        })

    today = date.today()
    error_message = None

    if request.method == 'POST':
        class_name = request.POST.get('class_name')
        selected_date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        meeting_link = request.POST.get('meeting_link')
        selected_course_id = request.POST.get('assigned_course')  # Get selected course ID from dropdown

        # Convert strings to appropriate date and time objects
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            error_message = "Invalid date or time format. Please use the correct format."
            return render(request, 'schedule_class.html', {
                'assigned_courses': assigned_courses,
                'today': today,
                'error_message': error_message
            })

        # Validate that the selected date is not in the past
        if selected_date < today:
            error_message = "The selected date cannot be in the past."
            return render(request, 'schedule_class.html', {
                'assigned_courses': assigned_courses,
                'today': today,
                'error_message': error_message
            })
        
        # Fetch the selected course to validate dates
        course = Course.objects.get(id=selected_course_id)  # Fetch the course by ID
        
        # Validate that the scheduled date is within the course's start and end dates
        if selected_date < course.starting_date or selected_date > course.ending_date:
            error_message = f"The scheduled date must be between {course.starting_date} and {course.ending_date}."
            return render(request, 'schedule_class.html', {
                'assigned_courses': assigned_courses,
                'today': today,
                'error_message': error_message
            })

        # Check that the end time is after the start time
        if end_time <= start_time:
            error_message = "End time must be after the start time."
            return render(request, 'schedule_class.html', {
                'assigned_courses': assigned_courses,
                'today': today,
                'error_message': error_message
            })
        
        # Overlap validation - Check if the new class conflicts with any existing scheduled classes for any teacher
        overlapping_classes = ClassSchedule.objects.filter(
            date=selected_date,
            start_time__lt=end_time,  # An overlap if the class starts before the new one ends
            end_time__gt=start_time   # And ends after the new one starts
        )

        if overlapping_classes.exists():
            error_message = "The scheduled class overlaps with an existing class scheduled by another teacher."
            return render(request, 'schedule_class.html', {
                'assigned_courses': assigned_courses,
                'today': today,
                'error_message': error_message
            })

        # Create the class schedule record in the database
        schedule = ClassSchedule(
            class_name=class_name,
            course_name=course,  # Use the fetched course
            date=selected_date,
            start_time=start_time,
            end_time=end_time,
            meeting_link=meeting_link,
            teacher=teacher
        )
        schedule.save()

        if schedule:
            return redirect('teacher_dashboard')  # Redirect to teacher's dashboard on success

    # Fetch scheduled classes for this teacher
    current_datetime = datetime.now()
    scheduled_classes = ClassSchedule.objects.filter(
        teacher=teacher, date__gte=today, end_time__gt=current_datetime.time()
    )

    return render(request, 'schedule_class.html', {
        'first_name': teacher.first_name,
        'last_name': teacher.last_name,
        'assigned_courses': assigned_courses,
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
        'future_classes': future_classes,
        'first_name': teacher.first_name,
        'last_name': teacher.last_name,  # Ongoing and future classes
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
from .models import ClassSchedule, CustomUser,Enrollment
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
# Fetch the enrolled courses for the student
    enrolled_courses = Enrollment.objects.filter(student=student)

    if not enrolled_courses.exists():
        messages.error(request, "You are not registered for any course.")
        return redirect('student_dashboard')

    # Get the current date and time in IST
    current_datetime = timezone.localtime()  # This will automatically convert to IST if TIME_ZONE is set to 'Asia/Kolkata'

    # Debug statement to check the current IST date and time
    print(f"Current date and time (IST): {current_datetime}")

    # Fetch ongoing and future classes for the registered course
    ongoing_future_classes = ClassSchedule.objects.filter(
       course_name__in=enrolled_courses.values_list('course', flat=True)  # Correct field name here
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
        teacher.date_of_birth = datetime.strptime(request.POST.get('date_of_birth'), '%Y-%m-%d').date()
        teacher.email = request.POST.get('email')
        teacher.contact = request.POST.get('contact')
        teacher.address_line1 = request.POST.get('address_line1')
        teacher.address_line2 = request.POST.get('address_line2')
        teacher.city = request.POST.get('city')
        teacher.state = request.POST.get('state')
        teacher.zip_code = request.POST.get('zip_code')
        teacher.qualification = request.POST.get('qualification')
        teacher.experience = request.POST.get('experience')

        # Handle file uploads
        if 'qualification_certificate' in request.FILES:
            teacher.qualification_certificate = request.FILES['qualification_certificate']
        if 'experience_certificate' in request.FILES:
            teacher.experience_certificate = request.FILES['experience_certificate']
        # Save the updated teacher details
        teacher.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('view_profile')  

    context = {'teacher': teacher,
               'first_name': teacher.first_name,
               'last_name': teacher.last_name,
        }
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
from django.shortcuts import render, redirect, get_object_or_404  # type: ignore
from django.contrib import messages  # For displaying messages
from .models import Material, Course, Teacher, TeacherCourse  # Import the TeacherCourse model

def upload_material(request):
    if request.method == 'POST':
        course_id = request.POST.get('course') 
        description = request.POST.get('description')  
        file = request.FILES.get('file') 

        # Get the teacher's ID from the session
        teacher_id = request.session.get('teacher_id')
        
        if teacher_id:
            # Fetch the courses assigned to the teacher
            assigned_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True)

            if int(course_id) in assigned_courses:  # Ensure the selected course is assigned to the teacher
                if file:
                    course = get_object_or_404(Course, id=course_id)
                    teacher = get_object_or_404(Teacher, id=teacher_id)  

                    # Attempt to create the Material object
                    try:
                        material = Material.objects.create(
                            teacher=teacher,  # Use the logged-in teacher from session
                            course=course,
                            file=file,
                            description=description
                        )
                        messages.success(request, 'Material uploaded successfully!')  # Success message
                        return redirect('teacher_dashboard')  # Redirect to dashboard after upload
                    except Exception as e:
                        messages.error(request, f'Error saving material: {str(e)}')  # Log the error
                else:
                    messages.error(request, 'Please upload a file.')  # Error for missing file
            else:
                messages.error(request, 'You do not have permission to upload material for this course.')  # Unauthorized course
        else:
            messages.error(request, 'You are not logged in as a teacher.')  # Not logged in

    # Fetch the list of courses assigned to the teacher to display in the form
    teacher_id = request.session.get('teacher_id')
    assigned_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True)
    courses = Course.objects.filter(id__in=assigned_courses)  # Get only assigned courses
    
    return render(request, 'upload_material.html', {'courses': courses})




from django.shortcuts import render, redirect, get_object_or_404  # type: ignore
from django.contrib import messages  # type: ignore
from .models import Material, CustomUser, Enrollment
from datetime import datetime
from django.utils import timezone

def view_materials(request):
    # Check if a CustomUser (student) is logged in by checking the session
    custom_user_id = request.session.get('custom_user_id')
    
    if not custom_user_id:
        messages.error(request, 'You must be logged in as a student to view materials.')
        return redirect('login')  # Redirect to login page if no session

    # Fetch the CustomUser (student) object using the session ID
    custom_user = get_object_or_404(CustomUser, id=custom_user_id)

    # Ensure the student is registered for any courses
    enrollments = Enrollment.objects.filter(student=custom_user)
    
    if not enrollments:
        messages.error(request, 'You are not registered for any course.')
        return redirect('student_dashboard')  # Redirect if no course is associated

    # Prepare a list to hold materials that meet the enrollment criteria
    materials = []
    
    # Loop through each enrollment to filter materials
    for enrollment in enrollments:
        # Combine enrollment_date and enrollment_time into a single datetime object
        if enrollment.enrollment_time:
            enrollment_datetime = datetime.combine(enrollment.enrollment_date, enrollment.enrollment_time)
        else:
            # Fallback if time is not present (you may adjust this as needed)
            enrollment_datetime = timezone.make_aware(datetime.combine(enrollment.enrollment_date, datetime.min.time()))
        
        # Make the combined datetime timezone-aware
        enrollment_datetime = timezone.make_aware(enrollment_datetime)
        
        # Fetch materials related to the course and filter by the enrollment datetime
        course_materials = Material.objects.filter(course=enrollment.course, uploaded_at__gte=enrollment_datetime)
        materials.extend(course_materials)

    # Render the materials in the template
    return render(request, 'view_materials.html', {'materials': materials})

# views.py
from .models import Material, Parent, CustomUser

def view_study_materials(request):

    parent = get_object_or_404(Parent, auto_generated_username=request.user.username)
    
    student = get_object_or_404(CustomUser, username=parent.student_username)

    materials = Material.objects.filter(course=student.course)
    
    return render(request, 'view_study_materials.html', {'materials': materials, 'student': student})

from django.shortcuts import render, redirect, get_object_or_404  # type: ignore
from django.utils import timezone  # type: ignore
from .models import Quizs, Course, TeacherCourse  # Import TeacherCourse for filtering

def create_quiz(request):
    teacher_id = request.session.get('teacher_id')  # Retrieve the teacher's ID from the session

    if not teacher_id:
        # Handle the case where the teacher is not logged in
        return redirect('login')

    # Fetch courses taught by the teacher
    assigned_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True)
    courses = Course.objects.filter(id__in=assigned_courses)  # Filter to only assigned courses

    if request.method == 'POST':
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        course = get_object_or_404(Course, id=course_id)
        
        # Create and save the quiz
        quiz = Quizs(course=course, teacher_id=teacher_id, title=title, 
                     start_date=start_date, end_date=end_date, 
                     start_time=start_time, end_time=end_time)
        quiz.save()

        return redirect('add_question', quiz_id=quiz.id)
    
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
from .models import CustomUser, Quizs, UserAnswers, Enrollment  # Ensure Enrollment is imported

def available_quizzes(request):
    custom_user_id = request.session.get('custom_user_id')

    if not custom_user_id:
        messages.error(request, "You are not logged in.")
        return redirect('login')

    try:
        student = CustomUser.objects.get(id=custom_user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('login')

    # Fetch enrollments for the student
    enrollments = Enrollment.objects.filter(student=student)

    if not enrollments.exists():
        messages.error(request, "You are not registered for any course.")
        return redirect('student_dashboard')

    current_datetime = timezone.localtime()

    # Create a list of enrolled courses with their enrollment dates and times
    enrolled_courses = [
        (enrollment.course, enrollment.enrollment_date, enrollment.enrollment_time)
        for enrollment in enrollments
    ]

    available_quizzes = []

    # Fetch quizzes that are ongoing or upcoming and have not ended
    for course, enrollment_date, enrollment_time in enrolled_courses:
        # Combine enrollment date and time to create a full datetime object
        enrollment_datetime = timezone.make_aware(datetime.combine(enrollment_date, enrollment_time or datetime.min.time()))

        # Fetch quizzes based on the course and check the date and time constraints
        quizzes_for_course = Quizs.objects.filter(
            course=course,
            start_date__lte=current_datetime.date(),
            end_date__gte=current_datetime.date(),
        ).filter(
            Q(start_time__lte=current_datetime.time()) | Q(start_date__gt=current_datetime.date())
        ).exclude(
            Q(end_date__lt=current_datetime.date()) | 
            (Q(end_date=current_datetime.date()) & Q(end_time__lt=current_datetime.time()))
        ).order_by('start_date', 'start_time')

        # Filter out quizzes that the student has already attempted
        quizzes_for_course = [quiz for quiz in quizzes_for_course if not UserAnswers.objects.filter(user=student, question__quiz=quiz).exists()]

        # Add the filtered quizzes to the available_quizzes list
        available_quizzes.extend(quizzes_for_course)

    return render(request, 'available_quizzes.html', {
        'quizzes': available_quizzes,
        'today': current_datetime.date(),
        'current_time': current_datetime.time()
    })



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

from django.shortcuts import render, redirect, get_object_or_404  # type: ignore
from django.http import HttpResponse  # type: ignore
from .models import Assignment, Course, Teacher, TeacherCourse  # Import the TeacherCourse model
from django.core.exceptions import ValidationError  # type: ignore
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
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()

            teacher_id = request.session.get('teacher_id')
            teacher = get_object_or_404(Teacher, id=teacher_id)

            assignment = Assignment(
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                file=file,
                course_name_id=course_name_id,
                teacher=teacher
            )

            if assignment.start_date > assignment.end_date:
                raise ValidationError("Start date cannot be after end date.")

            assignment.save()

            return redirect('teacher_dashboard')

        except ValidationError as e:
            return render(request, 'create_assignment.html', {
                'error': str(e),
                'courses': courses,  # Pass the courses to the template
                'assignment': request.POST
            })
        except Exception as e:
            return render(request, 'create_assignment.html', {
                'error': str(e),
                'courses': courses,
                'assignment': request.POST
            })

    # If not a POST request, get the assigned courses for the teacher
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, id=teacher_id)

    assigned_courses = TeacherCourse.objects.filter(teacher=teacher).select_related('course')
    courses = [tc.course for tc in assigned_courses]

    return render(request, 'create_assignment.html', {
        'courses': courses,
        'first_name': teacher.first_name,
        'last_name': teacher.last_name,
    })

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import datetime
from .models import Assignment, AssignmentSubmission, CustomUser, Enrollment  # Ensure to import Enrollment

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

    # Fetch the enrolled courses for the student along with the enrollment date and time
    enrollments = Enrollment.objects.filter(student=student)

    if not enrollments:
        messages.error(request, "You are not registered for any course.")
        return redirect('student_dashboard')

    # Create a list to store the courses and their enrollment date and time
    enrolled_courses_with_dates = [(enrollment.course, enrollment.enrollment_date, enrollment.enrollment_time) for enrollment in enrollments]

    # Create a list to hold the course names and the minimum enrollment datetime
    enrolled_courses = [course for course, _, _ in enrolled_courses_with_dates]
    
    # Fetch assignments based on the registered courses and filter by enrollment datetime
    current_date = timezone.now()
    assignment_details = []

    for course, enrollment_date, enrollment_time in enrolled_courses_with_dates:
        # Combine enrollment date and time to create a full datetime object
        if enrollment_time:
            enrollment_datetime = datetime.combine(enrollment_date, enrollment_time)
        else:
            enrollment_datetime = datetime.combine(enrollment_date, datetime.min.time())

        # Make the combined enrollment datetime timezone-aware
        enrollment_datetime = timezone.make_aware(enrollment_datetime)

        # Get assignments for the current course, considering enrollment datetime
        assignments = Assignment.objects.filter(course_name=course, start_date__gte=enrollment_datetime)

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
            assignment = Assignment.objects.filter(id=assignment_id, course_name__in=enrolled_courses).first()

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

        assigned_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True)
        courses = Course.objects.filter(id__in=assigned_courses)

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



from django.db.models import Subquery, OuterRef  # type: ignore
from django.shortcuts import render  # type: ignore
from .models import AssignmentSubmission, Course, TeacherCourse  # Import the TeacherCourse model

def evaluate_assignments(request):
    # Check if the teacher is logged in
    if 'teacher_id' in request.session:
        teacher_id = request.session['teacher_id']
        selected_course_id = request.GET.get('course_id')

        # Fetch all courses assigned to the teacher from the TeacherCourse table
        assigned_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True)
        courses = Course.objects.filter(id__in=assigned_courses)

        # Get the latest submission for each student
        latest_submissions = AssignmentSubmission.objects.filter(
            student=OuterRef('student'),
            assignment=OuterRef('assignment')
        ).order_by('-submitted_at')

        if selected_course_id:
            # Filter by course and ensure we only get the latest submission for each student
            submissions = AssignmentSubmission.objects.filter(
                assignment__course_name__id=selected_course_id,
                assignment__course_name__id__in=assigned_courses,  # Ensure the course is assigned to the teacher
                submitted_at=Subquery(latest_submissions.values('submitted_at')[:1])
            )
        else:
            # Get the latest submission for each student across all assigned courses
            submissions = AssignmentSubmission.objects.filter(
                assignment__course_name__id__in=assigned_courses,  # Ensure the course is assigned to the teacher
                submitted_at=Subquery(latest_submissions.values('submitted_at')[:1])
            )

        context = {
            'submissions': submissions,
            'courses': courses,
            'selected_course_id': selected_course_id,
            
            
        }
        return render(request, 'evaluate_assignment.html', context)
    else:
        return redirect('login')  # Redirect to login if the teacher is not authenticated

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


from django.shortcuts import render, redirect
from django.utils import timezone  # Ensure you have this imported
from .models import CalendarEvent, Course, TeacherCourse  # Import TeacherCourse for filtering

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
            courses = Course.objects.filter(id__in=TeacherCourse.objects.filter(teacher_id=request.session.get('teacher_id')).values_list('course_id', flat=True))
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

    # Fetch courses assigned to the teacher for the dropdown
    courses = Course.objects.filter(id__in=TeacherCourse.objects.filter(teacher_id=request.session.get('teacher_id')).values_list('course_id', flat=True))
    
    return render(request, 'add_event.html', {'courses': courses})  # Render the template with courses


from django.shortcuts import render
from .models import Course, CalendarEvent, TeacherCourse  # Import your models

def view_events(request):
    teacher_id = request.session.get('teacher_id')
    
    if not teacher_id:
        # Handle case where teacher_id is not found (e.g., redirect to login)
        return redirect('login')

    # Fetch courses assigned to the teacher
    assigned_courses = Course.objects.filter(id__in=TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True))
    
    # Fetch events created by the teacher for the assigned courses
    events = CalendarEvent.objects.filter(created_by_id=teacher_id, course_id__in=assigned_courses)

    return render(request, 'view_events.html', {
        'events': events,
        'courses': assigned_courses  # Pass only the courses assigned to the teacher to the template
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import CalendarEvent, Enrollment
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

def student_events(request):
    CustomUser = get_user_model()  # Fetch the custom user model
    custom_user_id = request.session.get('custom_user_id')

    if not custom_user_id:
        messages.error(request, 'You must be logged in as a student to view events.')
        return redirect('login')  # Redirect to login if no user session

    # Fetch the CustomUser (student) object using the session ID
    student = get_object_or_404(CustomUser, id=custom_user_id)

    # Fetch the enrollments for the student
    enrollments = Enrollment.objects.filter(student=student)

    if not enrollments.exists():
        messages.error(request, 'You are not registered for any courses.')
        return redirect('student_dashboard')  # Redirect if no enrollments are found

    # Create a list of enrolled courses with their enrollment dates and times
    enrolled_courses = [(enrollment.course, enrollment.enrollment_date, enrollment.enrollment_time) for enrollment in enrollments]

    # Current date and time for filtering events
    current_datetime = timezone.localtime()

    # Fetch events for the enrolled courses
    events = CalendarEvent.objects.filter(course__in=[course for course, _, _ in enrolled_courses])

    # Further filter events based on the enrollment date and time
    filtered_events = []
    for course, enrollment_date, enrollment_time in enrolled_courses:
        enrollment_datetime = timezone.make_aware(datetime.combine(enrollment_date, enrollment_time or datetime.min.time()))
        # Fetch events that start after the enrollment date and time
        filtered_events.extend(events.filter(course=course, start_time__gte=enrollment_datetime))

    # Filter by event type if provided in the GET request
    event_type = request.GET.get('event_type', '')
    if event_type:
        filtered_events = [event for event in filtered_events if event.event_type == event_type]

    context = {
        'events': filtered_events,
        'courses': [course for course, _, _ in enrolled_courses],  # Display course names
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
        'start_time': event.start_time.isoformat(),
        'end_time': event.end_time.isoformat(),
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


from django.shortcuts import render, redirect, get_object_or_404
from .models import Quizs, Course, Question, TeacherCourse  # Import TeacherCourse for filtering

def view_quiz_questions(request):
    teacher_id = request.session.get('teacher_id')  # Retrieve the teacher_id from the session

    if not teacher_id:
        # If the teacher is not logged in or the session has expired, redirect to the login page
        return redirect('login')

    # Fetch the courses taught by the teacher
    assigned_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True)
    courses = Course.objects.filter(id__in=assigned_courses)  # Only get the courses assigned to the teacher
    
    course_id = request.GET.get('course_id')  # Get the course ID from the query parameters

    # Fetch quizzes created by this teacher for their assigned courses
    quizzes = Quizs.objects.filter(teacher_id=teacher_id, course_id__in=assigned_courses)

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
from django.shortcuts import render, get_object_or_404  # type: ignore
from .models import Material, Course, TeacherCourse  # Import the TeacherCourse model

def view_uploaded_materials(request):
    # Assuming you have a session variable for the logged-in teacher
    teacher_id = request.session.get('teacher_id')

    # Fetch courses taught by the teacher
    assigned_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True)  # Get assigned course IDs
    courses = Course.objects.filter(id__in=assigned_courses)  # Get only assigned courses

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

from django.shortcuts import redirect
from django.utils import timezone
from .models import Attendance, ClassSchedule, CustomUser

def mark_attendance(request, schedule_id):
    custom_user_id = request.session.get('custom_user_id')
    if not custom_user_id:
        messages.error(request, "You need to log in to join the class.")
        return redirect('login')

    try:
        student = CustomUser.objects.get(id=custom_user_id)
        class_schedule = ClassSchedule.objects.get(id=schedule_id)
        current_time = timezone.localtime(timezone.now())
        print(current_time)
        # Check if the student is joining within the scheduled class time
        if class_schedule.start_time <= current_time.time() <= class_schedule.end_time and current_time.date() == class_schedule.date:
            # Mark attendance as present
            Attendance.objects.create(
                student=student,
                class_schedule=class_schedule,
                check_in_time=current_time,
                status='present'
            )
        else:
            # If the student tries to join outside the class time, mark them as absent
            Attendance.objects.create(
                student=student,
                class_schedule=class_schedule,
                check_in_time=current_time,
                status='absent'
            )

        # Redirect to the meeting link after marking attendance
        return redirect(class_schedule.meeting_link)

    except CustomUser.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('login')
    except ClassSchedule.DoesNotExist:
        messages.error(request, "Class schedule not found.")
        return redirect('student_dashboard')


from myApp.models import TeacherCourse, Enrollment, Course

def student_list(request):
    teacher_id = request.session.get('teacher_id')  # Assuming you're using session to manage teacher login

    # Get the courses assigned to this teacher
    teacher_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True)

    # Get students enrolled in those courses
    enrolled_students = Enrollment.objects.filter(course_id__in=teacher_courses).select_related('student')

    context = {
        'enrolled_students': enrolled_students,
    }
    return render(request, 'student_list.html', context)

from django.shortcuts import render
from myApp.models import TeacherCourse, Enrollment, Attendance, ClassSchedule

def view_attendance(request):
    teacher_id = request.session.get('teacher_id')
    # Get the courses assigned to this teacher
    teacher_courses = TeacherCourse.objects.filter(teacher_id=teacher_id).values_list('course_id', flat=True)

    # Get the class schedules for the courses
    class_schedules = ClassSchedule.objects.filter(course_name_id__in=teacher_courses)

    # Get the selected class schedule ID from the form
    selected_class_schedule_id = request.GET.get('class_schedule_id')

    # Initialize variables for attendance records and course name
    attendance_records = None
    course_name = None

    if selected_class_schedule_id:
        # Fetch attendance records based on the selected class schedule
        attendance_records = Attendance.objects.filter(class_schedule_id=selected_class_schedule_id)

        # Fetch the course name associated with the selected class schedule
        selected_class_schedule = ClassSchedule.objects.get(id=selected_class_schedule_id)
        course_name = selected_class_schedule.course_name  # Assuming 'course_name' is the field that holds the course

    context = {
        'class_schedules': class_schedules,
        'attendance_records': attendance_records,
        'selected_class_schedule': selected_class_schedule_id,
        'course_name': course_name,
    }

    return render(request, 'view_attendance.html', context)

def create_zoom_meeting(request):
    access_token = "eyJzdiI6IjAwMDAwMSIsImFsZyI6IkhTNTEyIiwidiI6IjIuMCIsImtpZCI6IjI5NGNjYjIwLWY3MDQtNDJhYS1iNzEyLTAxNGE0M2EyMzg2YyJ9.eyJhdWQiOiJodHRwczovL29hdXRoLnpvb20udXMiLCJ1aWQiOiJPR3pzdVV4M1M2aXBWblZPbS1QTF9RIiwidmVyIjoxMCwiYXVpZCI6IjEyYTlhY2Q5NDZlMTZlZDAxY2M3MjI5NGIyM2M2ZGQ5OGQxNGYwNTcwNWJjZjVjMjk4MjJlODJiY2ExMzRkNDQiLCJuYmYiOjE3Mjk3ODg0NjAsImNvZGUiOiJoem9vNXlGSFMxMnAtTktSd18yc0d3ejhOWDM4Z0pGRHQiLCJpc3MiOiJ6bTpjaWQ6OTV3MVQybmxTcE9XeXV4dTVHamg0dyIsImdubyI6MCwiZXhwIjoxNzI5NzkyMDYwLCJ0eXBlIjozLCJpYXQiOjE3Mjk3ODg0NjAsImFpZCI6ImJzNGhzUTZHUnRlOE8tRUhtRzh1RFEifQ.t3InXC_J95euY8WDhxopJeMnGmYCR9CHbqG7-my5stlGSaagaiX8AEh1YO5t24ZBzAMQ1l5Gd48C7OEibY8UaQ"
    url = "https://api.zoom.us/v2/users/me/meetings"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "topic": "class_name",
        "type": 2,
        "start_time": "start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),",
        "duration": 60,
        "timezone": "UTC",
        "settings": {
            "host_video": True,
            "participant_video": True,
            "join_before_host": True,  # Optional
            "mute_upon_entry": False
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 201:
        meeting_info = response.json()
        return render(request, 'zoom_meeting_created.html', {'meeting_info': meeting_info})
    else:
        return render(request, 'error.html', {'error': response.text})


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LeaveRequest, Course, CustomUser

def apply_leave(request):
    custom_user_id = request.session.get('custom_user_id')
    
    if not custom_user_id:
        messages.error(request, 'You need to log in to apply for leave.')
        return redirect('login')  # Redirect to login if session doesn't have a custom_user_id

    student = CustomUser.objects.get(id=custom_user_id)  # Fetch the CustomUser instance

    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        reason = request.POST.get('reason')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        course_id = request.POST.get('course_id')
        
        course = Course.objects.get(id=course_id)
        leave_request = LeaveRequest.objects.create(
            student=student,  # Using the CustomUser instance from the session
            course=course,
            leave_type=leave_type,
            reason=reason,
            start_date=start_date,
            end_date=end_date
        )
        messages.success(request, 'Leave request submitted successfully!')
        return redirect('student_dashboard')
    
    courses = Course.objects.all()  # Assuming students can select a course
    return render(request, 'apply_leave.html', {'courses': courses})


from django.shortcuts import render, get_object_or_404
from .models import LeaveRequest

def manage_leave_requests(request):
    leave_requests = LeaveRequest.objects.filter(status='pending')
    return render(request, 'manage_leave.html', {'leave_requests': leave_requests})

def update_leave_status(request, leave_id, status):
    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    leave_request.status = status
    leave_request.save()
    return redirect('teacher_dashboard')

def student_leave_requests(request):
    custom_user_id = request.session.get('custom_user_id')
    student = CustomUser.objects.get(id=custom_user_id)
    leave_requests = LeaveRequest.objects.filter(student=student)

    return render(request, 'student_leave_requests.html', {
        'leave_requests': leave_requests
    })

from .models import Group, Message, TeacherMessage, Course, CustomUser, Teacher
from django.shortcuts import render, get_object_or_404, redirect

def group_chat_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Fetch the user based on the session variable custom_user_id
    custom_user_id = request.session.get('custom_user_id') 
    if not custom_user_id:
        return redirect('login')  # Redirect to login if not authenticated via session

    user = get_object_or_404(CustomUser, id=custom_user_id)

    # Get or create the group for the course
    group, created = Group.objects.get_or_create(course=course)

    # Check if the user is a student or a teacher, and add them to the respective group if not already added
    if user:  
        if not group.students.filter(id=user.id).exists():
            group.students.add(user)

    # Handle new message submission
    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            Message.objects.create(group=group, sender=user, content=content)
            return redirect('group_chat', course_id=course_id)

    # Get all messages related to the group
    student_messages = group.messages.all().order_by('timestamp')
    teacher_messages = group.teacher_messages.all().order_by('timestamp')

    # Combine messages from both models
    all_messages = sorted(list(student_messages) + list(teacher_messages), key=lambda m: m.timestamp)

    return render(request, 'group_chat.html', {
        'group': group,
        'messages': all_messages,
        'user': user,  # Pass the user to the template if needed
    })



def discussion_forum(request):
    custom_user_id = request.session.get('custom_user_id')
    enrolled_courses = Course.objects.filter(enrollments__student_id=custom_user_id)
    

    return render(request,'discussion_forum.html',{'enrolled_courses':enrolled_courses})


from .models import Group, TeacherMessage, Course
from django.shortcuts import render, get_object_or_404, redirect

def teacher_group_chat_view(request, course_id):
    teacher_id = request.session.get('teacher_id')

    if not teacher_id:
        return redirect('login')

    course = get_object_or_404(Course, id=course_id)
    group = get_object_or_404(Group, course=course)

    # Get all messages and combine them
    student_messages = group.messages.all()
    teacher_messages = group.teacher_messages.all()

    # Combine and sort all messages
    all_messages = list(student_messages) + list(teacher_messages)
    all_messages.sort(key=lambda x: x.timestamp)  # Sort by timestamp

    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            # Create a message for teachers
            TeacherMessage.objects.create(group=group, teacher=teacher, content=content)
            return redirect('teacher_group_chat', course_id=course_id)

    return render(request, 'teacher_group_chat.html', {
        'group': group,
        'messages': all_messages,  # Pass the combined messages to the template
        'teacher': teacher,
    })


from django.shortcuts import render, get_object_or_404
from .models import TeacherCourse

def teacher_discussion_forum(request):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('login')  # Redirect to login if not authenticated

    # Get all courses assigned to the teacher
    assigned_courses = TeacherCourse.objects.filter(teacher_id=teacher_id)

    return render(request, 'teacher_discussion_forum.html', {'assigned_courses': assigned_courses})
