# Generated by Django 5.1.6 on 2025-03-09 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('host_app', '0006_hostavailability'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hostavailability',
            name='visitor',
        ),
        migrations.AddConstraint(
            model_name='hostavailability',
            constraint=models.CheckConstraint(condition=models.Q(('end_time__gt', models.F('start_time'))), name='end_time_after_start_time'),
        ),
    ]
