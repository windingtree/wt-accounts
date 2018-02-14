import pickle, zlib
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
from django.shortcuts import render, resolve_url, redirect
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django.core.cache import cache

from accounts import etherscan
from accounts.forms import LoginForm, RegistrationForm, ProfileForm, VerifyForm
from accounts.models import send_login_email, User, EthAddressHistory, OnfidoCall, send_verification_status_email

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
        return HttpResponseRedirect(reverse('login_sent'))

    return render(request, 'accounts/login.html', {'form': form})


def login_token_expired(request):
    return render(request, 'accounts/login_expired.html')


def home(request):
    return render(request, 'home.html')


def faq(request):
    return render(request, 'accounts/faq.html')


def registration(request):
    if is_from_banned_country(request):
        return HttpResponseRedirect(reverse('geofence'))

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
        messages.warning(request, 'Please fill all the fields')
        return HttpResponseRedirect(reverse('profile'))

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

    return render(request, 'accounts/status.html', {'form': form})


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
        if not test:
            oc = OnfidoCall.objects.filter(type='check', onfido_id=check_id).first()
            send_verification_status_email(request, oc.user)
    return HttpResponse('OK')


@login_required
def eth_sums(request):
    store_to_profiles = request.method == 'POST' and request.user.is_staff
    if store_to_profiles:
        logger.debug('Storing contributions to users')

    users = User.objects.exclude(eth_address='')
    users_by_eth_address = {u.eth_address.lower(): u for u in users}
    # because it is about 50 http calls to the api and the object is around 6mb
    # the cache is set in management command `fill_user_eth_contrib`
    all_transactions = []
    all_transactions_cache = cache.get(etherscan.CACHE_KEY)
    if all_transactions_cache:
        all_transactions = pickle.loads(zlib.decompress(all_transactions_cache))
    transactions = etherscan.filter_failed(all_transactions)
    total = etherscan.eth_get_total(transactions)
    sum_for_accounts = etherscan.get_sum_for_accounts(transactions, users_by_eth_address.keys())
    unique_contributions = etherscan.get_unique_contributions(transactions)
    unique_contributions_sum = int(sum( v for (a,v) in unique_contributions.items() )) / 10**18
    registered_contributions = [ (a,v) for (a,v) in sum_for_accounts.items() if v > 0 ]
    registered_contributions_sum = int(sum( v for (a,v) in sum_for_accounts.items() )) / 10**18

    unique_contributions_sorted = [
        (x, int(y)/10**18, y) for x,y in
        sorted(unique_contributions.items(), key=lambda x: -x[1])
    ]
    sum_for_accounts_sorted = [
        (x, int(y)/10**18, y) for x,y in
        sorted(sum_for_accounts.items(), key=lambda x: -x[1])
    ]

    for account, sum_ in sum_for_accounts.items():
        users_by_eth_address[account].eth_sum = sum_
        if store_to_profiles:
            users_by_eth_address[account].eth_contrib = str(sum_)
            users_by_eth_address[account].save(update_fields=['eth_contrib'])

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
        'total': total,
        'total_eth': int(total)/10**18,
        'users': users,
    }
    return render(request, 'accounts/eth_sums.html', context)

def is_from_banned_country(request):
    banned_countries = ['US', 'CHINA']
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

