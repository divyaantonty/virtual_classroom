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
    
    path('register/', views.register, name='register'),
    path('teachers/', views.teachers_view, name='teachers'),
    path('recover/', views.recover_view, name='recover'),
    path('features/', views.features, name='features'),
    path('parent/', views.parent, name='parent'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('register-teacher/', views.register_teacher, name='register_teacher'),
    path('approve-teacher/<int:teacher_id>/', views.approve_teacher, name='approve_teacher'),

    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('scheduled-classes/', views.view_scheduled_classes, name='view_scheduled_classes'),
    
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('schedule-class/', views.schedule_class, name='schedule_class'),

    path('parent_dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('view-class-schedule/', views.view_class_schedule, name='view_class_schedule'),

    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-students/', views.manage_students, name='manage_students'),

    path('manage-teachers/', views.manage_teachers, name='manage_teachers'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('approve_teachers/', views.approve_teacher, name='approve_teachers'),
    path('approve_teacher/<int:teacher_id>/', views.approve_teacher, name='approve_teacher'),
    path('reject_teacher/<int:teacher_id>/', views.reject_teacher, name='reject_teacher'),
    path('remove_teacher/<int:teacher_id>/', views.remove_teacher, name='remove_teacher'),


    path('password_reset/', views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/',views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
