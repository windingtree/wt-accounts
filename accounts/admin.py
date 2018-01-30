from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'eth_contrib')


class OnfidoCallAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'type', 'status', 'result')
    list_filter = ('type', 'status', 'result')


admin.site.register(User, CustomUserAdmin)
admin.site.register(OnfidoCall, OnfidoCallAdmin)
