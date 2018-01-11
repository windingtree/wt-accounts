import logging

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, resolve_url
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from account.forms import LoginForm, RegistrationForm
from account.models import send_login_email

logger = logging.getLogger(__name__)


@sensitive_post_parameters()
@never_cache
def login_token(request, uidb64, token):
    # the token has validity for settings.PASSWORD_RESET_TIMEOUT_DAYS
    assert uidb64 is not None and token is not None  # checked by URLconf
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        logger.debug('Logging in user=%s', user)
        auth_login(request, user)
        return HttpResponseRedirect(resolve_url(settings.LOGIN_REDIRECT_URL))
    else:
        logger.warning('Denied access for  uidb64=%s, token=%s, user=%s', uidb64, token, user)
        return HttpResponseForbidden()


def login(request):
    form = LoginForm(request.POST or None)

    if form.is_valid():
        user = form.user
        if user:
            logger.debug('Sending email to %s', user.email)
            send_login_email(request, user)
        else:
            logger.warning('Attempt to login with non-existent email %s',
                           form.cleaned_data['email'])
        return HttpResponseRedirect(reverse('login_sent'))

    return render(request, 'account/login.html', {'form': form})


def registration(request):
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        logger.debug('Registering new user %s', user.email)

        logger.debug('Sending email to %s', user.email)
        send_login_email(request, user)

        return HttpResponseRedirect(reverse('login_sent'))

    return render(request, 'account/registration.html', {'form': form})
