from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.db import models

# Create your models here.
from django.template import Template
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def create_link_context(user, use_https=False):
    # 'use_https': request.is_secure()
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
    email_content = render_to_string('account/email_login.txt', context=context, request=request)
    # sending to settings.DEFAULT_FROM_EMAIL
    user.email_user('WT login', email_content)
