import pytz
import pickle, zlib
import hashlib
import hmac
import json
import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, resolve_url, redirect
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.utils import timezone

from accounts import etherscan
from accounts.forms import LoginForm, RegistrationForm, ProfileForm, VerifyForm
from accounts.models import send_login_email, User, EthAddressHistory, OnfidoCall, send_verification_status_email

logger = logging.getLogger(__name__)

def is_ico_running():
    ico_end = pytz.timezone("UTC").localize(datetime(2018, 2, 15, 0, 0))
    return timezone.now() < ico_end

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
        if request.user.is_authenticated and request.user != user:
            logger.warning('User %s just logged in as another user %s', request.user, user)
        auth_login(request, user)
        return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        logger.warning('Denied access for  uidb64=%s, token=%s, user=%s', uidb64, token, user)
        return redirect('login_token_expired')


def geofence(request):
    return render(request, 'geofence.html')


def login(request):
    form = LoginForm(request.POST or None)

    if form.is_valid():
        user = form.user
        logger.debug('Sending email to %s', user.email)
        send_login_email(request, user)
        return redirect('login_sent')

    if is_ico_running():
        template = 'accounts/login.html'
    else:
        template = 'accounts/login-end.html'
    return render(request, template, {'form': form})


def login_token_expired(request):
    return render(request, 'accounts/login_expired.html')


def home(request):
    if is_ico_running():
        template = 'home.html'
    else:
        template = 'home-kyc-in-progress.html'
    return render(request, template)


def faq(request):
    return render(request, 'accounts/faq.html')


def registration(request):
    if is_from_banned_country(request):
        return redirect('geofence')

    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    form = RegistrationForm(request.POST or None)
    # data-sitekey
    form.recaptcha_site_key = settings.RECAPTCHA_SITE_KEY
    if form.is_valid():
        user = form.save()
        logger.debug('Registering new user %s', user.email)

        logger.debug('Sending email to %s', user.email)
        send_login_email(request, user)

        return redirect('login_sent')

    if is_ico_running():
        template = 'accounts/registration.html'
    else:
        template = 'accounts/registration-end.html'
    return render(request, template, {'form': form})


@login_required
def status(request):
    if not request.user.can_verify() or request.user.eth_address == '':
        messages.warning(request, 'Please fill all the fields')
        return redirect('profile')

    onfido_sent = request.user.verify_status

    form = VerifyForm(request.POST or None, request.FILES or None, instance=request.user,
                      send_to_onfido=not onfido_sent)
    if request.method == 'POST':
        if onfido_sent:
            if form.is_valid(): # so we store the image upload
                form.save()
            request.user.last_check.check_reload()
            messages.error(request,
                           'Current verification status: {}'.format(onfido_sent))
            return redirect('status')
        elif form.is_valid():
            form.save()
            onfido_check = form.onfido_check
            messages.success(request, mark_safe(
                'Verification request sent, please check your '
                'inbox or visit <a target="_blank" href="{0}">{0}</a>'.format(
                    onfido_check.check_form_url)))
            return redirect('status')

    if is_ico_running():
        template = 'accounts/status.html'
    else:
        template = 'accounts/status-end.html'
    return render(request, template, {'form': form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    old_eth_address = request.user.eth_address
    if form.is_valid():
        messages.success(request, 'Your profile was updated')
        EthAddressHistory.objects.create(user=request.user, eth_address=old_eth_address)
        form.save()
        return redirect('status')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, 'You were logged out')
    return redirect(settings.LOGOUT_REDIRECT_URL)


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
        if not test:
            oc = OnfidoCall.objects.filter(type='check', onfido_id=check_id).first()
            send_verification_status_email(request, oc.user)
    return HttpResponse('OK')


def get_all_transactions_context():
    # because it is about 50 http calls to the api and the object is around 6mb
    # the cache is set in management command `fill_user_eth_contrib`
    all_transactions = []
    all_transactions_cache = cache.get(etherscan.CACHE_KEY)
    if all_transactions_cache:
        all_transactions = pickle.loads(zlib.decompress(all_transactions_cache))

    users = User.objects.exclude(eth_address='')
    users_by_eth_address = {u.eth_address.lower(): u for u in users}

    transactions = etherscan.filter_failed(all_transactions)
    total = etherscan.eth_get_total(transactions)

    sum_for_accounts = etherscan.get_sum_for_accounts(transactions, users_by_eth_address.keys())

    unique_contributions = etherscan.get_unique_contributions(transactions)
    unique_contributions_sum = int(sum( v for (a,v) in unique_contributions.items() )) / 10**18

    registered_contributions = dict( (a,v) for (a,v) in sum_for_accounts.items() if v > 0 )
    registered_contributions_sum = int(sum( v for (a,v) in registered_contributions.items() )) / 10**18

    non_registered_contributions = dict( (a,v) for (a,v) in unique_contributions.items() if a not in sum_for_accounts )
    non_registered_contributions_sum = int(sum( v for (a,v) in non_registered_contributions.items() )) / 10**18

    unique_contributions_sorted = [
        (x, int(y)/10**18, y) for x,y in
        sorted(unique_contributions.items(), key=lambda x: -x[1])
    ]
    sum_for_accounts_sorted = [
        (x, int(y)/10**18, y) for x,y in
        sorted(sum_for_accounts.items(), key=lambda x: -x[1])
    ]
    non_registered_contributions_sorted = [
        (x, int(y)/10**18, y) for x,y in
        sorted(non_registered_contributions.items(), key=lambda x: -x[1])
    ]

    context = {
        'all_transactions': all_transactions,
        'transactions': transactions,
        'unique_contributions': unique_contributions,
        'unique_contributions_sorted': unique_contributions_sorted,
        'unique_contributions_sum': unique_contributions_sum,
        'sum_for_accounts': sum_for_accounts,
        'sum_for_accounts_sorted': sum_for_accounts_sorted,
        'registered_contributions': registered_contributions,
        'registered_contributions_sum': registered_contributions_sum,
        'non_registered_contributions': non_registered_contributions,
        'non_registered_contributions_sum': non_registered_contributions_sum,
        'non_registered_contributions_sorted': non_registered_contributions_sorted,
        'total': total,
        'total_eth': int(total)/10**18,
        'users': users,
    }
    return context

@login_required
def eth_sums(request):
    context = get_all_transactions_context()
    return render(request, 'accounts/eth_sums.html', context)

def unregistered_accounts(request):
    not_to_refund = [
        '0xfbb1b73c4f0bda4f67dca266ce6ef42f520fbb98',
        '0x5f6f3c6178ab90c8121d2a27fd7df9c18f3f9006',
        '0x0681d8db095565fe8a346fa0277bffde9c0edbbf',
        '0x0271753b5e8482d2e3b9bfb40b40b1d5038f0fee',
        '0xd12db5c2f965e75451c7e0414c9dd6a5993efe52',
        '0x2b5634c42055806a59e9107ed44d43c426e58258',
        '0x7edc93e8ba7a68267baee46359c4976060216269',
        '0xbcf02404ac2163507a7913aba42cf770d1acb71b',
        '0x9af008948e28c08f15a10a033e67378a215ebbf7',
        '0xda54ff10706a5ed10976910e77c064c185dda8cf',
        '0xea4775e5bdf85efbe31a8c5815f0cb136c82982d',
        '0xbc3fc679aa38b3dd0502a04008addb6dd8ae2121',
        '0x2a7616c5cb2a883235ff67070e54c2024936642f',
        '0x2e0e074c5102287ea57e06137d97935d139a0125',
        '0x32a8b132bbe70ed1edfae2a8ada567f171776d16',
        '0xb1b090276696eb40c956f520691672d0949a3563',
        '0x7040285f8dc8a13939a3266622d883ec59a21576',
        '0x390de26d772d2e2005c6d1d24afc902bae37a4bb',
    ]
    context = get_all_transactions_context()
    to_refund = dict(
        (k,v) for (k,v) in context['non_registered_contributions'].items()
        if k not in not_to_refund
    )
    to_refund_sum = int(sum( v for (a,v) in to_refund.items() )) / 10**18
    to_refund_sorted = [
        (x, int(y)/10**18, y) for x,y in
        sorted(to_refund.items(), key=lambda x: x[1])
    ]

    context.update({
        'to_refund': to_refund,
        'to_refund_sum': to_refund_sum,
        'to_refund_sorted': to_refund_sorted,
    })
    return render(request, 'accounts/unregistered_accounts.html', context)

def is_from_banned_country(request):
    banned_countries = ['US',]
    geoip_header = request.META.get('HTTP_CF_IPCOUNTRY', '')
    return geoip_header.upper() in banned_countries

def headers(request):
    forbidden = ['US', 'CZ']
    geoip = 'HTTP_CF_IPCOUNTRY'
    lines = [
        '{}{}{}: {}{}{}'.format(
            '<strong>' if geoip == key else '',
            '<font color=red>' if request.META[key] in forbidden else '',
            key,
            request.META[key],
            '</font>' if request.META[key] in forbidden else '',
            '</strong>' if geoip == key else '',
        ) for key in request.META
    ]
    data = '\n'.join(lines)
    return HttpResponse('<pre>{}</pre>'.format(data))
