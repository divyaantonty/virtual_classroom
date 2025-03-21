# Generated by Django 5.1 on 2025-01-24 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0046_teacherstudent'),
    ]

    operations = [
        migrations.AddField(
            model_name='useranswers',
            name='attempt_date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='useranswers',
            name='grade',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='useranswers',
            name='marks_obtained',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='useranswers',
            name='percentage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
