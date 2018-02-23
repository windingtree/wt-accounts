from django.contrib import admin
from django.utils.html import format_html
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
            ('15-20', _('ETH contrib 15-20')),
            ('20+', _('ETH contrib 20+')),
        )

    def queryset(self, request, queryset):
        one_eth = len(str(10 ** 18))
        ten_eth = one_eth + 1
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
                    eth_contrib__startswith=14), eth_contrib_length=ten_eth)
        elif self.value() == '15-20':
            return queryset.filter(
                Q(eth_contrib__startswith=15) | Q(eth_contrib__startswith=16) | Q(
                    eth_contrib__startswith=17) | Q(eth_contrib__startswith=18) | Q(
                    eth_contrib__startswith=19),
                eth_contrib_length=ten_eth)
        elif self.value() == '20+':
            return queryset.filter(Q(
                Q(eth_contrib_length__gt=ten_eth) |
                Q(
                    Q(eth_contrib__startswith=2) | Q(eth_contrib__startswith=3) | \
                    Q(eth_contrib__startswith=4) | Q(eth_contrib__startswith=5) | \
                    Q(eth_contrib__startswith=6) | Q(eth_contrib__startswith=7) | \
                    Q(eth_contrib__startswith=8) | Q(eth_contrib__startswith=9),
                    eth_contrib_length=ten_eth,
                )
            ))


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


class EthAddressHistoryInline(admin.TabularInline):
    model = EthAddressHistory
    extra = 0

class OnfidoCallInline(admin.TabularInline):
    model = OnfidoCall
    extra = 0


class CustomUserAdmin(UserAdmin):
    search_fields = ['username', 'email', 'first_name', 'last_name', 'eth_address']

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
                    'is_verified', 'onfido_link',
                    'proof_of_address_status', 'proof_of_address_file',
                    'eth_address_link',
                    'previous_eth_address_link',
                    'last_login', 'date_joined',
                    )
    list_filter = ('is_staff', 'is_superuser', 'proof_of_address_status',
                   EthContribFilter, KYCVerified)

    inlines = [OnfidoCallInline, EthAddressHistoryInline]

    def eth_address_link(self, obj):
        if obj.eth_address:
            return format_html(
                    '<a href="https://etherscan.io/address/{eth_address}">{eth_address}</a>',
                    eth_address=obj.eth_address,
                )
        return '-'
            
    def previous_eth_address_link(self, obj):
        ethaddresses = obj.ethaddresses.exclude(eth_address='').exclude(eth_address=obj.eth_address)
        if ethaddresses.count():
            return format_html(
                    '<a href="https://etherscan.io/address/{eth_address}">{eth_address}</a>',
                    eth_address=ethaddresses.first().eth_address
                )
        return '-'

    def onfido_link(self, obj):
        check = obj.last_check
        if not check:
            return '[none]'
        return format_html(
                '<a href="{results_uri}">{status} {result}</a>',
                results_uri = check.response['results_uri'],
                status=check.status,
                result=check.result,
            )
    onfido_link.short_description = 'onfido link'


class OnfidoCallAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'type', 'status', 'result')
    list_filter = ('type', 'status', 'result')


admin.site.register(User, CustomUserAdmin)
admin.site.register(OnfidoCall, OnfidoCallAdmin)
