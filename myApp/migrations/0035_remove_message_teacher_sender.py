# Generated by Django 5.1 on 2024-10-26 03:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0034_message_teacher_sender'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='teacher_sender',
        ),
    ]
