import logging

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.json import JSONField
from django_extensions.db.models import TimeStampedModel

from accounts import onfido_api

logger = logging.getLogger(__name__)


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    eth_address = models.CharField(_('ETH address'), max_length=100, blank=True)

    def can_verify(self):
        return self.first_name and self.last_name and self.email

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

    def onfido_check(self):
        applicant = onfido_api.create_applicant(self)
        OnfidoCall.objects.create(user=self, type='applicant', applicant_id=applicant.id,
                                  response=applicant.to_dict())
        check = onfido_api.check(applicant.id)
        return OnfidoCall.objects.create(user=self, type='check', response=check.to_dict(),
                                         applicant_id=applicant.id, status=check.status or '',
                                         result=check.result or '')


class OnfidoCall(TimeStampedModel):
    TYPES = (
        ('applicant', 'applicant'),
        ('check', 'check'),
    )
    user = models.ForeignKey(User, related_name='onfidos', on_delete=models.DO_NOTHING)
    type = models.CharField(choices=TYPES, max_length=20)
    response = JSONField()
    status = models.CharField(blank=True, max_length=20)
    result = models.CharField(blank=True, max_length=20)
    applicant_id = models.CharField(blank=True, max_length=40)

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
                                         result=check.result or '')


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
    # sending to settings.DEFAULT_FROM_EMAIL
    user.email_user('WT login', email_content)
