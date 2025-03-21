# Generated by Django 5.1 on 2024-10-13 06:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0009_feedbackquestion_feedback'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalendarEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('description', models.TextField(blank=True)),
                ('event_type', models.CharField(max_length=50)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myApp.course')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myApp.teacher')),
            ],
        ),
    ]
