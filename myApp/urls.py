from django.urls import path
from myApp import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
)
urlpatterns = [
    path('', views.index_view, name='index'),
    path('about/', views.about_view, name='about'),
    path('admissions/', views.admissions_view, name='admissions'),
    
    path('contact/', views.contact_view, name='contact'),
    path('view-messages/', views.view_messages, name='view_messages'),
    path('reply-message/<int:message_id>/', views.reply_message, name='reply_message'),

    path('courses/', views.courses_view, name='courses'),

    path('add_courses/', views.add_course, name='add_courses'), 
    path('course_list/', views.course_list, name='course_list'), 

    path('course/10/', views.course_detail_10, name='course_detail_10'),
    path('course/higher-secondary/', views.course_detail_higher_secondary, name='course_detail_higher_secondary'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout, name='logout'),
    path('change_password/', views.change_password, name='change_password'),
    path('teacher_changepassword/', views.teacher_changepassword, name='teacher_changepassword'),
    path('teacher_updateprofile/', views.teacher_updateprofile, name='teacher_updateprofile'),
    
    path('register/', views.register, name='register'),
    path('teachers/', views.teachers_view, name='teachers'),
    path('recover/', views.recover_view, name='recover'),
    path('features/', views.features, name='features'),
    path('parent/', views.parent, name='parent'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('register-teacher/', views.register_teacher, name='register_teacher'),
    path('approve-teacher/<int:teacher_id>/', views.approve_teacher, name='approve_teacher'),

    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('view-scheduled-classes/', views.view_scheduled_classes, name='view_scheduled_classes'),
    path('view-materials/', views.view_materials, name='view_materials'),
    path('available_quizzes/', views.available_quizzes, name='available_quizzes'),
    path('view_quiz/<int:quiz_id>/', views.view_quiz, name='view_quiz'),
    path('assignment_detail/', views.assignment_detail, name='assignment_detail'),
    


    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('schedule-class/', views.schedule_class, name='schedule_class'),
    path('view_teacher_schedule_class/', views.view_teacher_schedule_class, name='view_teacher_schedule_class'),
    path('edit_class/', views.edit_class, name='edit_class'),
    path('view_profile/', views.view_profile, name='view_profile'),
    path('upload_material/', views.upload_material, name='upload_material'),
    path('create_quiz/', views.create_quiz, name='create_quiz'),
    path('add_question/<int:quiz_id>/', views.add_question, name='add_question'),
    path('create_assignment/', views.create_assignment, name='create_assignment'),
    

    path('parent_dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('view-class-schedule/', views.view_class_schedule, name='view_class_schedule'),
    path('parent_update_profile/', views.parent_update_profile, name='parent_update_profile'),
    path('view_study_materials/', views.view_study_materials, name='view_study_materials'),


    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-students/', views.manage_students, name='manage_students'),
    path('delete_student/<int:student_id>/', views.delete_student, name='delete_student'),


    path('manage-teachers/', views.manage_teachers, name='manage_teachers'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('approve_teachers/', views.approve_teacher, name='approve_teachers'),
    path('interview-teacher/', views.interview_teacher, name='interview_teacher'),
    path('reject_teacher/<int:teacher_id>/', views.reject_teacher, name='reject_teacher'),
    path('delete_teacher/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),

    path('feedback/teacher/', views.feedback_to_teacher, name='feedback_teacher'),
    path('feedback/student/', views.feedback_to_student, name='feedback_student'),


    path('password_reset/', views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/',views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)