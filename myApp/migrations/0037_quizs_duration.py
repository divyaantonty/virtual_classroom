# Generated by Django 5.1 on 2024-10-26 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0036_teachermessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizs',
            name='duration',
            field=models.IntegerField(default=30, help_text='Duration of the quiz in minutes'),
        ),
    ]
