# Generated by Django 3.2.7 on 2021-10-11 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0024_programmingexercise_same_course_programmingexercise_text_unique'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='questiontrainingsessionthroughmodel',
            constraint=models.UniqueConstraint(fields=('training_session', 'position'), name='same_session_unique_position'),
        ),
    ]
