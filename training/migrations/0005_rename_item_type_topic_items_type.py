# Generated by Django 3.2.6 on 2021-08-04 18:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0004_auto_20210804_1838'),
    ]

    operations = [
        migrations.RenameField(
            model_name='topic',
            old_name='item_type',
            new_name='items_type',
        ),
    ]
