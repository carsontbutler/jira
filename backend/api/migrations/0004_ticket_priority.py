# Generated by Django 4.0.3 on 2022-04-16 02:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_ticket_assignee'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='priority',
            field=models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('highest', 'Highest')], default='medium', max_length=20),
        ),
    ]