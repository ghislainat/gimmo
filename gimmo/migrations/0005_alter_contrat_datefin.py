# Generated by Django 4.0.6 on 2022-08-03 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gimmo', '0004_alter_contrat_datefin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contrat',
            name='datefin',
            field=models.DateField(blank=True, null=True),
        ),
    ]
