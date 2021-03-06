# Generated by Django 3.0.5 on 2020-05-15 18:12

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0017_auto_20200515_2006'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='membership',
            options={'verbose_name': 'Mitgliedschaft', 'verbose_name_plural': 'Mitgliedschaften'},
        ),
        migrations.AlterField(
            model_name='membership',
            name='partial',
            field=models.PositiveIntegerField(default=0, verbose_name='tlw. richtig'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='right',
            field=models.PositiveIntegerField(default=0, verbose_name='richtig'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='wrong',
            field=models.PositiveIntegerField(default=0, verbose_name='falsch'),
        ),
        migrations.AlterUniqueTogether(
            name='membership',
            unique_together={('user', 'team')},
        ),
    ]
