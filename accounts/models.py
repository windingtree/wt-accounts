from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    birth_date = models.DateField(_('date of birth'), blank=True, null=True)
    country = models.CharField(_('country'), blank=True, max_length=100)
    building_number = models.CharField(blank=True, max_length=100)
    street = models.CharField(blank=True, max_length=100)
    town = models.CharField(blank=True, max_length=100)
    postcode = models.CharField(blank=True, max_length=100)
    eth_address = models.CharField(_('eth_address'), max_length=100, blank=True)


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
