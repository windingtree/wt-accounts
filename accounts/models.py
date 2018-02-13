import logging

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import RegexValidator
from django.db import models
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from django_extensions.db.fields.json import JSONField
from django_extensions.db.models import TimeStampedModel
from django_s3_storage.storage import S3Storage

from accounts import onfido_api

logger = logging.getLogger(__name__)

validate_eth_address = RegexValidator(
    r'^(0x)?[0-9a-fA-F]{40}$',
    _("Enter a valid ethereum address, example: '0x4a4ac8d0b6a2f296c155c15c2bcaf04641818b78'"),
    'invalid'
)


class User(AbstractUser):
    PROOF_CHOICES = (
        ('unchecked', 'unchecked'),
        ('valid', 'valid'),
        ('failed', 'failed'),
    )
    email = models.EmailField(_('email address'), unique=True)
    mobile = models.CharField(_('mobile'), max_length=30)
    birth_date = models.DateField(_('date of birth'), null=True,
                                  help_text='Accepted format is YYYY-MM-DD')
    country = CountryField(_('Country'))
    building_number = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    town = models.CharField(_('City'), max_length=100)
    postcode = models.CharField(max_length=100)
    eth_address = models.CharField(_('Your ERC20 Ethereum wallet address from which you’ll be '
                                     'sending your contribution. It can\'t be an exchange address!'),
                                   max_length=100, validators=[validate_eth_address])
    eth_contrib = models.CharField(blank=True, max_length=30)
    proof_of_address_file = models.FileField(_('Proof of address'), storage=S3Storage(),
                                             null=True, upload_to='proof_of_address')
    proof_of_address_status = models.CharField(max_length=20, choices=PROOF_CHOICES,
                                               default=PROOF_CHOICES[0][0])

    def can_verify(self):
        must = ('first_name', 'last_name', 'birth_date', 'mobile', 'street',
                'building_number', 'town', 'postcode', 'country')
        return all(getattr(self, f) for f in must)

    @property
    def last_check(self):
        return self.onfidos.filter(type='check').first()

    @property
    def verify_status(self):
        check = self.last_check
        return check.status if check else None

    def is_verified(self):
        check = self.last_check
        return check.result == 'clear' if check else False
    is_verified.boolean = True  # django admin

    def onfido_check(self):
        applicant = onfido_api.create_applicant(self)
        OnfidoCall.objects.create(user=self, type='applicant', applicant_id=applicant.id,
                                  onfido_id=applicant.id, response=applicant.to_dict())
        check = onfido_api.check(applicant.id)
        return OnfidoCall.objects.create(user=self, type='check', response=check.to_dict(),
                                         applicant_id=applicant.id, status=check.status or '',
                                         onfido_id=check.id, result=check.result or '')

    @property
    def eth_contrib_int(self):
        return int(self.eth_contrib or 0)

    def eth_contrib_eth(self):
        return self.eth_contrib_int / 10**18
    eth_contrib_eth.short_description = 'eth contrib [eth]'

class OnfidoCall(TimeStampedModel):
    TYPES = (
        ('applicant', 'applicant'),
        ('check', 'check'),
        ('webhook', 'webhook'),
    )
    user = models.ForeignKey(User, related_name='onfidos', on_delete=models.DO_NOTHING)
    type = models.CharField(choices=TYPES, max_length=20)
    response = JSONField()
    status = models.CharField(blank=True, max_length=20)
    result = models.CharField(blank=True, max_length=20)
    applicant_id = models.CharField(blank=True, max_length=40)
    onfido_id = models.CharField(max_length=40)

    class Meta:
        ordering = ['-created']
        get_latest_by = 'created'

    @property
    def check_form_url(self):
        return self.response.get('form_uri')

    def check_reload(self):
        logger.debug('calling check reload for user %s', self.user)
        if self.type != 'check':
            logger.error('Calling check reload on non check OnfidoCall %s', self.id)
            raise AssertionError('Calling check reload on non check OnfidoCall')
        check = onfido_api.check_reload(self.applicant_id, self.response['id'])
        return OnfidoCall.objects.create(user=self.user, type='check', response=check.to_dict(),
                                         applicant_id=self.applicant_id, status=check.status or '',
                                         onfido_id=check.id, result=check.result or '')


def create_link_context(user, use_https=False):
    return {
        'email': user.email,
        'domain': settings.DOMAIN,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'user': user,
        'token': default_token_generator.make_token(user),
        'protocol': 'https' if use_https else 'http',
    }


def send_login_email(request, user):
    context = create_link_context(user, use_https=request.is_secure())
    email_content = render_to_string('accounts/email_login.txt', context=context, request=request)
    # sending from settings.DEFAULT_FROM_EMAIL
    html_message = render_to_string('accounts/email_login.html', context=context, request=request)
    user.email_user('Your Winding Tree Account', email_content, html_message=html_message)


def send_verification_status_email(request, user):
    context = create_link_context(user, use_https=request.is_secure())
    email_content = render_to_string('accounts/email_verification_status.txt', context=context, request=request)
    html_message = render_to_string('accounts/email_verification_status.html', context=context, request=request)
    # sending from settings.DEFAULT_FROM_EMAIL
    user.email_user('WT verification status', email_content, html_message=html_message)


def reload_users_onfido_checks():
    for user in User.objects.all().iterator():
        current_status = user.verify_status
        if user.verify_status:
            user.last_check.check_reload()
            logger.debug('Reloaded onfido for user: %s initial status: %s, new status: %s', user,
                         current_status, user.verify_status)

