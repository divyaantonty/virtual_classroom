# Generated by Django 5.1 on 2024-10-22 15:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0021_message'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Message',
        ),
    ]