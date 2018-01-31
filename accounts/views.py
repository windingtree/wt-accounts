import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse, \
    HttpResponseBadRequest
from django.shortcuts import render, resolve_url
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from accounts import etherscan
from accounts.forms import LoginForm, RegistrationForm, ProfileForm, VerifyForm
from accounts.models import send_login_email, User, OnfidoCall, send_verification_status_email

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
        return HttpResponseRedirect(resolve_url('status'))
    else:
        logger.warning('Denied access for  uidb64=%s, token=%s, user=%s', uidb64, token, user)
        return HttpResponseRedirect(reverse('login_token_expired'))


def login(request):
    form = LoginForm(request.POST or None)

    if form.is_valid():
        user = form.user
        logger.debug('Sending email to %s', user.email)
        send_login_email(request, user)
        return HttpResponseRedirect(reverse('login_sent'))

    return render(request, 'accounts/login.html', {'form': form})


def login_token_expired(request):
    return render(request, 'accounts/login_expired.html')


def home(request):
    return render(request, 'home.html')


def registration(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(resolve_url(settings.LOGIN_REDIRECT_URL))

    form = RegistrationForm(request.POST or None)
    # data-sitekey
    form.recaptcha_site_key = settings.RECAPTCHA_SITE_KEY
    if form.is_valid():
        user = form.save()
        logger.debug('Registering new user %s', user.email)

        logger.debug('Sending email to %s', user.email)
        send_login_email(request, user)

        return HttpResponseRedirect(reverse('login_sent'))

    return render(request, 'accounts/registration.html', {'form': form})


@login_required
def status(request):
    if not request.user.can_verify() or request.user.eth_address == '':
        return HttpResponseRedirect(reverse('profile'))
    return render(request, 'accounts/status.html')


@login_required
def profile(request):
    verify = 'verify' in request.POST
    if verify:
        form = ProfileForm(instance=request.user)
        if not request.user.can_verify():
            messages.error(request, 'All the fields must be filled for verification')
        elif request.user.verify_status:
            request.user.last_check.check_reload()
            messages.error(request,
                           'Current verification status: {}'.format(request.user.verify_status))
        else:
            verify_form = VerifyForm(request.POST, user=request.user)
            if verify_form.is_valid():
                onfido_check = verify_form.onfido_check
                messages.success(request, mark_safe(
                    'Verification request sent, please check your '
                    'inbox or visit <a target="_blank" href="{0}">{0}</a>'.format(
                        onfido_check.check_form_url)))
            return render(request, 'accounts/profile.html',
                          {'form': form, 'verify_form': verify_form})
        return HttpResponseRedirect(reverse('profile'))
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        messages.success(request, 'Your profile was updated')
        form.save()
        return HttpResponseRedirect(reverse('profile'))
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, 'You were logged out')
    return HttpResponseRedirect(reverse(settings.LOGOUT_REDIRECT_URL))


@require_POST
@csrf_exempt
def onfido_webhook(request):
    logger.debug('Incomming webhook %s', request.body)
    test = b'"resource_type":"test_resource"' in request.body
    expected_signature = request.META.get('HTTP_X_SIGNATURE', '')
    digest = hmac.new(settings.ONFIDO_WEBHOOK_TOKEN.encode('ascii'), request.body,
                      hashlib.sha1).hexdigest()
    if not test and expected_signature != digest:
        logger.error('Differing signatures expected %s actual %s', expected_signature, digest)
        return HttpResponseBadRequest(
            'Differing signatures expected %s actual %s' % (expected_signature, digest))
    body = json.loads(request.body.decode('utf-8'))
    if body['payload']['action'] in {'check.completed', }:
        check_id = body['payload']['object']['id']
        oc = OnfidoCall.objects.get(type='check', onfido_id=check_id)
        send_verification_status_email(request, oc.user)
    return HttpResponse('OK')


@login_required
def eth_sums(request):
    store_to_profiles = request.method == 'POST' and request.user.is_staff
    if store_to_profiles:
        logger.debug('Storing contributions to users')
    users = User.objects.exclude(eth_address='')
    users_by_eth_address = {u.eth_address: u for u in users}
    transactions = etherscan.get_transactions()
    total = etherscan.eth_get_total(transactions)
    sum_for_accounts = etherscan.get_sum_for_accounts(transactions, users_by_eth_address.keys())
    for account, sum in sum_for_accounts.items():
        users_by_eth_address[account].eth_sum = sum
        if store_to_profiles:
            users_by_eth_address[account].eth_contrib = str(sum)
            users_by_eth_address[account].save(update_fields=['eth_contrib'])
    return render(request, 'accounts/eth_sums.html', {'total': total, 'users': users})
