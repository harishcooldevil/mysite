# Generated by Django 2.2.5 on 2020-04-17 05:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='liked_comments',
            field=models.TextField(default='[]'),
        ),
    ]
