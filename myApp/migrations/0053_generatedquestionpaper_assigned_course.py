# Generated by Django 5.1 on 2025-02-01 14:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0052_remove_resourcebookmark_resource_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='generatedquestionpaper',
            name='assigned_course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='myApp.course'),
        ),
    ]
