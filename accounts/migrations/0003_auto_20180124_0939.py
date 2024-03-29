# Generated by Django 2.0.1 on 2018-01-24 09:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20180122_1841'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnfidoCall',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('type', models.CharField(choices=[('applicant', 'applicant'), ('check', 'check')], max_length=20)),
                ('response', django_extensions.db.fields.json.JSONField(default=dict)),
                ('status', models.CharField(blank=True, max_length=20)),
                ('result', models.CharField(blank=True, max_length=20)),
                ('applicant_id', models.CharField(blank=True, max_length=40)),
            ],
            options={
                'ordering': ['created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.RemoveField(
            model_name='user',
            name='birth_date',
        ),
        migrations.RemoveField(
            model_name='user',
            name='building_number',
        ),
        migrations.RemoveField(
            model_name='user',
            name='country',
        ),
        migrations.RemoveField(
            model_name='user',
            name='postcode',
        ),
        migrations.RemoveField(
            model_name='user',
            name='street',
        ),
        migrations.RemoveField(
            model_name='user',
            name='town',
        ),
        migrations.AlterField(
            model_name='user',
            name='eth_address',
            field=models.CharField(blank=True, max_length=100, verbose_name='ETH address'),
        ),
        migrations.AddField(
            model_name='onfidocall',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='onfidos', to=settings.AUTH_USER_MODEL),
        ),
    ]
