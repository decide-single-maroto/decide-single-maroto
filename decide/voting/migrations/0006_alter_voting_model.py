# Generated by Django 4.1 on 2023-11-13 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0005_voting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voting',
            name='model',
            field=models.CharField(choices=[('IDENTITY', 'Identity'), ('DHONDT', "D'hondt")], default='IDENTITY', max_length=8),
        ),
    ]
