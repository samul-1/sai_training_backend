# Generated by Django 3.2.7 on 2021-10-04 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0017_exercisesubmission_error'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='uses_programming_exercises',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='testcaseoutcomethroughmodel',
            name='details',
            field=models.JSONField(blank=True),
        ),
    ]
