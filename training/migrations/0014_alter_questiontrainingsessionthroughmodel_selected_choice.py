# Generated by Django 3.2.7 on 2021-09-14 10:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0013_trainingtemplaterule_topic_template_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questiontrainingsessionthroughmodel',
            name='selected_choice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='training.choice'),
        ),
    ]