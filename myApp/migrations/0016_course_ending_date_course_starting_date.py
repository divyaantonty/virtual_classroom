# Generated by Django 5.1 on 2024-10-19 15:08

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0015_remove_teacher_assigned_course_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='ending_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='starting_date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]