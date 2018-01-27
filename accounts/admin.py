from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin


class OnfidoCallAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'type', 'status', 'result')
    list_filter = ('type', 'status', 'result')


admin.site.register(User, UserAdmin)
admin.site.register(OnfidoCall, OnfidoCallAdmin)
