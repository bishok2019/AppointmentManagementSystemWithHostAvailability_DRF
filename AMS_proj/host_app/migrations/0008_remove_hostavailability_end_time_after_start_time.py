# Generated by Django 5.1.6 on 2025-03-10 08:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('host_app', '0007_remove_hostavailability_visitor_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='hostavailability',
            name='end_time_after_start_time',
        ),
    ]
