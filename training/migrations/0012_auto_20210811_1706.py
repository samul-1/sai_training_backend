# Generated by Django 3.2.6 on 2021-08-11 17:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0011_questiontrainingsessionthroughmodel_position'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programmingexercise',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='programmingexercises', to='training.course'),
        ),
        migrations.AlterField(
            model_name='programmingexercise',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='programmingexercises', to='training.topic'),
        ),
        migrations.AlterField(
            model_name='question',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='questions', to='training.course'),
        ),
        migrations.AlterField(
            model_name='question',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='questions', to='training.topic'),
        ),
        migrations.AlterField(
            model_name='questiontrainingsessionthroughmodel',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.question'),
        ),
        migrations.AlterField(
            model_name='questiontrainingsessionthroughmodel',
            name='training_session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.trainingsession'),
        ),
    ]
