# Generated by Django 5.1 on 2024-09-20 05:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0005_teacher_registration_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teacher',
            name='registration_code',
        ),
    ]