# Generated by Django 3.0.5 on 2020-05-02 19:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_auto_20200502_2109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='round',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.Round', verbose_name='Runde'),
        ),
    ]