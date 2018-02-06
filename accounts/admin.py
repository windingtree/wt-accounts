from django.contrib import admin
from django.db.models import Q
from django.db.models.functions import Length

from .models import *
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _


class EthContribFilter(admin.SimpleListFilter):
    title = _('ETH contrib amount')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'eth_contrib_requires_KYC'

    def lookups(self, request, model_admin):
        return (
            ('0', _('ETH contrib == 0')),
            ('0-1', _('ETH contrib < 1')),
            ('1-2', _('ETH contrib 1-2')),
            ('2-5', _('ETH contrib 2-5')),
            ('5-9', _('ETH contrib 5-9')),
            ('10-15', _('ETH contrib 10-15')),
            ('15+', _('ETH contrib 15+')),
        )

    def queryset(self, request, queryset):
        one_eth = len(str(10 ** 18))
        queryset = queryset.annotate(eth_contrib_length=Length('eth_contrib'))

        if self.value() == '0':
            return queryset.filter(eth_contrib='')
        elif self.value() == '0-1':
            return queryset.filter(eth_contrib_length__lt=one_eth).exclude(eth_contrib='')
        elif self.value() == '1-2':
            return queryset.filter(eth_contrib_length=one_eth, eth_contrib__startswith=1)
        elif self.value() == '2-5':
            return queryset.filter(Q(eth_contrib__startswith=2) | Q(eth_contrib__startswith=3) | Q(
                eth_contrib__startswith=4), eth_contrib_length=one_eth)
        elif self.value() == '5-9':
            return queryset.filter(Q(eth_contrib__startswith=5) | Q(eth_contrib__startswith=6) | Q(
                eth_contrib__startswith=7) | Q(eth_contrib__startswith=8) | Q(
                eth_contrib__startswith=9), eth_contrib_length=one_eth)
        elif self.value() == '10-15':
            return queryset.filter(
                Q(eth_contrib__startswith=10) | Q(eth_contrib__startswith=11) | Q(
                    eth_contrib__startswith=12) | Q(eth_contrib__startswith=13) | Q(
                    eth_contrib__startswith=14), eth_contrib_length=one_eth + 1)
        elif self.value() == '15+':
            return queryset.filter(Q(
                Q(eth_contrib__startswith=15) | Q(eth_contrib__startswith=16) | Q(
                    eth_contrib__startswith=17) | Q(eth_contrib__startswith=18) | Q(
                    eth_contrib__startswith=19) | Q(eth_contrib__startswith=2),
                eth_contrib_length=one_eth + 1) | Q(eth_contrib_length__gt=one_eth + 1))


class KYCVerified(admin.SimpleListFilter):
    title = _('KYC verified')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'kyc_verified'

    def lookups(self, request, model_admin):
        return (
            ('started', _('KYC started')),

        )

    def queryset(self, request, queryset):
        if self.value() == 'started':
            return queryset.filter(onfidos__type='check').distinct()


class OnfidoCallInline(admin.TabularInline):
    model = OnfidoCall
    extra = 0


class CustomUserAdmin(UserAdmin):
    def eth_contrib_eth(self, obj):
        value = obj.eth_contrib or 0
        return int(value) / 10**18
    eth_contrib_eth.short_description = 'eth contrib [eth]'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'mobile')}),
        (_('Address'), {'fields': ('country', ('postcode', 'town'), ('street', 'building_number'))}),
        (_('Proof of address'), {'fields': ('proof_of_address_file', 'proof_of_address_status')}),
        (_('ICO'), {'fields': ('eth_address', 'eth_contrib')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('birth_date', 'last_login', 'date_joined')}),
    )

    list_display = ('username', 'first_name', 'last_name', 'is_staff',
                    'eth_contrib_eth',
                    'is_verified', 'onfido_status', 'onfido_result',
                    'proof_of_address_status', 'proof_of_address_file',
                    'eth_address')
    list_filter = ('is_staff', 'is_superuser', 'proof_of_address_status',
                   EthContribFilter, KYCVerified)

    inlines = [OnfidoCallInline]

class OnfidoCallAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'type', 'status', 'result')
    list_filter = ('type', 'status', 'result')


admin.site.register(User, CustomUserAdmin)
admin.site.register(OnfidoCall, OnfidoCallAdmin)
