from django.core.management.base import BaseCommand, CommandError

from accounts import models

class Command(BaseCommand):
    help = 'Update onfido statuses for those that started KYC'

    def handle(self, *args, **options):
        models.reload_users_onfido_checks()

