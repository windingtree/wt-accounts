from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin


class OnfidoCallAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(OnfidoCall, OnfidoCallAdmin)
