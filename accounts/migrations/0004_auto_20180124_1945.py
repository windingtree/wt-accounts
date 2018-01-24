# Generated by Django 2.0.1 on 2018-01-24 19:45

from django.db import migrations, models
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20180124_0939'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='onfidocall',
            options={'get_latest_by': 'created', 'ordering': ['-created']},
        ),
        migrations.AddField(
            model_name='user',
            name='birth_date',
            field=models.DateField(blank=True, null=True, verbose_name='date of birth'),
        ),
        migrations.AddField(
            model_name='user',
            name='building_number',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='country',
            field=django_countries.fields.CountryField(blank=True, max_length=2, verbose_name='country'),
        ),
        migrations.AddField(
            model_name='user',
            name='mobile',
            field=models.CharField(blank=True, max_length=30, verbose_name='mobile'),
        ),
        migrations.AddField(
            model_name='user',
            name='postcode',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='street',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='town',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]