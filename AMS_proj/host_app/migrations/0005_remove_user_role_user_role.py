# Generated by Django 5.1.6 on 2025-02-21 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('host_app', '0004_remove_user_user_type'),
        ('role_app', '0002_alter_permission_created_by_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.ManyToManyField(blank=True, related_name='role', to='role_app.role'),
        ),
    ]
