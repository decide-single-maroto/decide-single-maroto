# Generated by Django 4.1 on 2023-11-15 10:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desc', models.TextField()),
                ('cattegory', models.CharField(choices=[('YES/NO', 'yes/no'), ('OPTIONS', 'options')], default='', max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='Voting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('desc', models.TextField(blank=True, null=True)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('model', models.CharField(choices=[('IDENTITY', 'Identity'), ('DHONDT', "D'hondt")], default='IDENTITY', max_length=8)),
                ('seats', models.PositiveIntegerField(blank=True, null=True)),
                ('tally', models.JSONField(blank=True, null=True)),
                ('postproc', models.JSONField(blank=True, null=True)),
                ('auths', models.ManyToManyField(related_name='votings', to='base.auth')),
                ('pub_key', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='voting', to='base.key')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='voting', to='voting.question')),
            ],
        ),
        migrations.CreateModel(
            name='QuestionOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(blank=True, null=True)),
                ('option', models.TextField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='voting.question')),
            ],
        ),
    ]
