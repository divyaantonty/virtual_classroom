# Generated by Django 5.1 on 2025-02-14 04:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0063_remove_studentfacedata_face_encoding_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentfacedata',
            name='face_image',
            field=models.ImageField(upload_to='face_images/'),
        ),
    ]
