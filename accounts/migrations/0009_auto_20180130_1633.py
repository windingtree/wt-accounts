# Generated by Django 2.0.1 on 2018-01-30 16:33

from django.db import migrations, models
import django_s3_storage.storage


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_auto_20180130_1039'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='non_us_resident',
        ),
        migrations.RemoveField(
            model_name='user',
            name='terms_accepted',
        ),
        migrations.AlterField(
            model_name='user',
            name='proof_of_address_file',
            field=models.FileField(blank=True, null=True, storage=django_s3_storage.storage.S3Storage(), upload_to='proof_of_address', verbose_name='Proof of address'),
        ),
    ]
