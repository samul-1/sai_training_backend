# Generated by Django 3.2.6 on 2021-08-09 12:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='course',
        ),
    ]