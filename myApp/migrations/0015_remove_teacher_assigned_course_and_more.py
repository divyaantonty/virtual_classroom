# Generated by Django 5.1 on 2024-10-19 13:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0014_rename_course_batch_enrollment_course'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teacher',
            name='assigned_course',
        ),
        migrations.RemoveField(
            model_name='teacher',
            name='teaching_area',
        ),
        migrations.CreateModel(
            name='TeacherCourse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teaching_area', models.CharField(max_length=255)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_teachers', to='myApp.course')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_courses', to='myApp.teacher')),
            ],
            options={
                'unique_together': {('teacher', 'course')},
            },
        ),
    ]
