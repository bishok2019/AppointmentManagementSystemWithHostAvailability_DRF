# Generated by Django 5.1.6 on 2025-03-07 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visitor_app', '0003_rename_meeting_time_visitor_meeting_start_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitor',
            name='meeting_end_time',
            field=models.TimeField(),
        ),
    ]
