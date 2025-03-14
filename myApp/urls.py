from django.urls import include, path
from myApp import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
    course_enrollment_view,
  
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
    path('assignment_detail/', views.assignment_submission_view, name='assignment_detail'),

    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('available_quizzes/', views.available_quizzes, name='available_quizzes'),
    path('quiz/<int:quiz_id>/', views.quiz_questions, name='quiz_questions'),
    path('quiz/submit/<int:quiz_id>/', views.submit_quiz, name='submit_quiz'),
    path('quiz/<int:quiz_id>/', views.quiz_result, name='quiz_result'),
    
    path('feedback/', views.feedback_view, name='feedback_form'),
    path('available-courses/', views.available_courses, name='available_courses'),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),

    path('assigned_courses/', views.assigned_courses, name='assigned_courses'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('schedule-class/', views.schedule_class, name='schedule_class'),
    path('view_teacher_schedule_class/', views.view_teacher_schedule_class, name='view_teacher_schedule_class'),
    path('edit_class/', views.edit_class, name='edit_class'),
    path('view_profile/', views.view_profile, name='view_profile'),
    path('upload_material/', views.upload_material, name='upload_material'),
    path('create_quiz/', views.create_quiz, name='create_quiz'),
    path('add_question/<int:quiz_id>/', views.add_question, name='add_question'),
    path('create_assignment/', views.create_assignment, name='create_assignment'),
    path('view_assignment/', views.view_assignment, name='view_assignment'),
    path('evaluate_assignment/', views.evaluate_assignments, name='evaluate_assignment'),
    path('submit-grade/<int:submission_id>/', views.submit_grade, name='submit_grade'),
    path('view_uploaded_materials/', views.view_uploaded_materials, name='view_uploaded_materials'),

    path('parent_dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('view-class-schedule/', views.view_class_schedule, name='view_class_schedule'),
    path('parent_update_profile/', views.parent_update_profile, name='parent_update_profile'),
    path('view_study_materials/', views.view_study_materials, name='view_study_materials'),
   

    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-students/', views.manage_students, name='manage_students'),
    path('delete_student/<int:student_id>/', views.delete_student, name='delete_student'),
    path('add_feedback_question/', views.add_feedback_question, name='add_feedback_question'),
    path('view_feedback_responses/', views.view_feedback_responses, name='view_feedback_responses'),
    path('toggle-student-status/<int:student_id>/', views.toggle_student_status, name='toggle_student_status'),
    path('edit_course/<int:course_id>/', views.edit_course, name='edit_course'),

    path('manage-teachers/', views.manage_teachers, name='manage_teachers'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('approve_teachers/<int:teacher_id>/', views.approve_teacher, name='approve_teachers'),
    path('interview-teacher/', views.interview_teacher, name='interview_teacher'),
    path('reject_teacher/<int:teacher_id>/', views.reject_teacher, name='reject_teacher'),
    path('delete_teacher/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),


    path('password_reset/', views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/',views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    path('add_event/', views.add_event, name='add_event'),
    path('view_event/', views.view_events, name='view_events'),
    path('student_event/', views.student_events, name='student_event'),
    path('events/filtered/', views.filtered_events, name='filtered_events'),


    path('view_quiz_questions/', views.view_quiz_questions, name='view_quiz_questions'),
    path('view_student_answers/', views.view_student_answers, name='view_student_answers'),
    path('toggle_teacher_status/<int:teacher_id>/', views.toggle_teacher_status, name='toggle_teacher_status'),
    path('mark_attendance/<int:schedule_id>/', views.mark_attendance, name='mark_attendance'),

    path('student_list/', views.student_list, name='student_list'),

    path('view_attendance/', views.view_attendance, name='view_attendance'),

    path('create_meeting/', views.create_zoom_meeting, name='create_meeting'),

    path('apply-leave/', views.apply_leave, name='apply_leave'),
    path('manage_leave/', views.manage_leave_requests, name='manage_leave'),
    path('update-leave-status/<int:leave_id>/<str:status>/', views.update_leave_status, name='update_leave_status'),

    path('student_leave_requests/', views.student_leave_requests, name='student_leave_requests'),
    path('course/<int:course_id>/group-chat/', views.group_chat_view, name='group_chat'),
    path('discussion_forum/', views.discussion_forum, name='discussion_forum'),

    path('teacher/<int:course_id>/group-chat/', views.teacher_group_chat_view, name='teacher_group_chat'),
    path('teacher_discussion_forum/', views.teacher_discussion_forum, name='teacher_discussion_forum'),
    path('enroll/details/<int:course_id>/', views.enrollment_details, name='enrollment_details'),
    path('enroll/confirm/<int:course_id>/', views.confirm_enrollment, name='confirm_enrollment'),

    path('register_event/<int:event_id>/', views.register_event, name='register_event'),
    path('teacher/interview_details/<int:teacher_id>/', views.view_interview_details, name='view_interview_details'),
    
    path('assign_students/', views.assign_students_to_teacher, name='assign_students_to_teacher'),
    path('assign_students/<int:teacher_id>/', views.select_course_for_teacher, name='select_course_for_teacher'),
    path('assign_students/<int:teacher_id>/<int:course_id>/', views.assign_students, name='assign_students_with_course'),
    
    path('check-course-name/', views.check_course_name, name='check_course_name'),
    path('upload/', views.upload_material, name='upload_material'),
    path('course-enrollment/', views.course_enrollment_view, name='course_enrollment'),  # New URL for course enrollment
    path('evaluate-answers/', views.evaluate_answers, name='evaluate_answers'),
    

    # path('student_performance_dashboard/', views.student_performance_dashboard, name='student_performance_dashboard'),
    path('chatbot/', views.chatbot_response, name='chatbot_response'),
    path('generate-image/', views.generate_image, name='generate_image'),
    
    path('student_performance/', views.student_performance_view, name='student_performance'),
    path('quiz_marks/', views.quiz_marks_view, name='quiz_marks'),
    path('certificate_template/<int:course_id>/', views.generate_certificate, name='certificate_template'),
    
    path('question-generator/', views.question_generator, name='question_generator'),
    path('generate-question/', views.generate_question, name='generate_question'),
    path('question-papers/', views.view_question_papers, name='view_question_papers'),
    path('delete-paper/<int:paper_id>/', views.delete_question_paper, name='delete_question_paper'),
    path('download-paper/<int:paper_id>/', views.download_question_paper, name='download_question_paper'),

    path("search_books", views.search_books, name="search_books"),

    path('translate-material/', views.translate_material, name='translate_material'),

    path('generate-summary/', views.generate_summary, name='generate_summary'),

    path('log-violation/', views.log_violation, name='log_violation'),

    path('question-bank/<int:course_id>/', views.question_bank, name='question_bank'),


    path('check-final-exam-eligibility/', views.check_final_exam_eligibility, name='check_final_exam_eligibility'),
    path('start-final-exam/<int:course_id>/', views.start_final_exam, name='start_final_exam'),

    path('exam-results/<int:exam_id>/', views.exam_results, name='exam_results'),
    
    path('final-exam-setup/<int:course_id>/', views.final_exam_setup, name='final_exam_setup'),
    path('take-final-exam/<int:exam_id>/', views.take_final_exam, name='take_final_exam'),
    path('submit-exam/<int:exam_id>/', views.submit_exam, name='submit_exam'),
    path('ping/', views.ping, name='ping'),
    path('check-existing-exam/<int:course_id>/', views.check_existing_exam, name='check_existing_exam'),

    path('face-capture/', views.face_capture_view, name='face_capture'),
    path('save-face-data/', views.save_face_data, name='save_face_data'),

    path('whiteboard/', views.whiteboard, name='whiteboard'),

    path('verify-face-attendance/<int:schedule_id>/', views.verify_face_and_mark_attendance, name='verify_face_attendance'),

    path('message-center/', views.parent_message_center, name='parent_message_center'),
    path('send-parent-message/', views.send_parent_message, name='send_parent_message'),
    path('mark-message-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),

    path('group/<int:group_id>/upload-media/', views.upload_media_message, name='upload_media_message'),
    
    path('share-whiteboard/', views.share_whiteboard, name='share_whiteboard'),

    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('send-event-suggestion/', views.send_event_suggestion, name='send_event_suggestion'),
    path('get-event-suggestions/<int:event_id>/', views.get_event_suggestions, name='get_event_suggestions'),

    path('save-mind-map/', views.save_mind_map, name='save_mind_map'),
    path('get-mind-maps/', views.get_mind_maps, name='get_mind_maps'),
    path('delete-mind-map/<int:map_id>/', views.delete_mind_map, name='delete_mind_map'),

    path('text-to-speech/<int:material_id>/', views.text_to_speech, name='text_to_speech'),

    path('create-note/', views.create_note, name='create_note'),
    path('view-notes/', views.view_notes, name='view_notes'),
    path('edit-note/<int:note_id>/', views.edit_note, name='edit_note'),
    path('delete-note/<int:note_id>/', views.delete_note, name='delete_note'),
    path('download-note-pdf/<int:note_id>/', views.download_note_pdf, name='download_note_pdf'),

    path('view-event-registrations/', views.view_event_registrations, name='view_event_registrations'),
    path('export-registrations/', views.export_registrations, name='export_registrations'),

    path('teacher_messages/', views.teacher_messages, name='teacher_messages'),

    path('send-teacher-reply/', views.send_teacher_reply, name='send_teacher_reply'),

    

    path('get-message-history/<int:message_id>/', views.get_message_history, name='get_message_history'),


    path('check-material-exists/', views.check_material_exists, name='check_material_exists'),

    path('get-course-students/', views.get_course_students, name='get_course_students'),
    path('send-message-to-parent/', views.send_message_to_parent, name='send_message_to_parent'),

    path('process-ocr/', views.process_ocr, name='process_ocr'),

    path('check-plagiarism/<int:submission_id>/', views.check_plagiarism, name='check_plagiarism'),
    path('check-ai-content/<int:submission_id>/', views.check_ai_content, name='check_ai_content'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)