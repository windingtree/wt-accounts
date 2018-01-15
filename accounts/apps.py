from django.apps import AppConfig

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class AccountConfig(AppConfig):
    name = 'accounts'

admin.site.register(User, UserAdmin)
