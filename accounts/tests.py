# Create your tests here.
from pprint import pprint
from unittest.mock import Mock

import pytest
from datetime import date

from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.forms import model_to_dict
from django.urls import reverse

from accounts import onfido_api
from accounts.etherscan import eth_get_total, get_transactions, get_sum_for_accounts
from accounts.forms import RegistrationForm
from accounts.models import create_link_context, send_login_email, User, OnfidoCall

EMAIL = 'tester@test.cz'

# will be equal to everything, usefull for ids and dates
everything_equals = type('omnieq', (), {"__eq__": lambda x, y: True})()


# TODO test confusable stuff a bit

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username=EMAIL, email=EMAIL)


@pytest.fixture
def onfido_test_user(db):
    return User.objects.create_user(
        username=EMAIL, email=EMAIL, first_name='Caligula', last_name='Tesla',
        birth_date=date(1980, 1, 1), building_number='100', street='Main Street',
        town='London', postcode='SW4 6EH', country='GBR', mobile='+420777619338'
    )


@pytest.mark.django_db
def test_RegistrationForm(monkeypatch):
    form = RegistrationForm()
    assert form.is_valid() == False

    form = RegistrationForm(data={'email': EMAIL.upper()})
    assert form.is_valid() == False  # recaptcha..
    assert form.errors['g_recaptcha_response'][0] == 'reCAPTCHA required'

    # lets patch requests and the response to fail
    monkeypatch.setattr("requests.post", lambda url, data: Mock(
        **{'json.return_value': {'success': False, 'error-codes': ['server error']}}))
    form = RegistrationForm(data={'email': EMAIL.upper(), 'g-recaptcha-response': '...'})
    assert form.is_valid() == False  # recaptcha..
    assert form.errors['g_recaptcha_response'][0] == "reCAPTCHA - ['server error']"

    # lets patch requests and the response FTW
    monkeypatch.setattr("requests.post", lambda url, data: Mock(
        **{'json.return_value': {'success': True}}))
    form = RegistrationForm(data={'email': EMAIL.upper(), 'g-recaptcha-response': '...'})
    assert form.is_valid()

    user = form.save()
    user_data = model_to_dict(user)

    assert user_data.pop('password').startswith('!')
    assert user_data.pop('date_joined')
    assert user_data == {
        'email': 'tester@test.cz',  # is lowercase
        'first_name': '',
        'groups': [],
        'id': everything_equals,
        'is_active': True,
        'is_staff': False,
        'is_superuser': False,
        'last_login': None,
        'last_name': '',
        'user_permissions': [],
        'username': 'tester@test.cz',
        'birth_date': None,
        'building_number': '',
        'country': '',
        'mobile': '',
        'postcode': '',
        'street': '',
        'town': '',
        'eth_address': '',
    }


def test_create_link_context(test_user):
    context = create_link_context(test_user)
    assert len(context.pop('token')) == 24
    assert context == {
        'domain': 'localhost:8000',
        'email': 'tester@test.cz',
        'protocol': 'http',
        'uid': 'MQ',
        'user': test_user
    }


def test_send_login_email(rf, settings, test_user):
    rf.is_secure = lambda: True
    # settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

    send_login_email(rf, test_user)
    m = mail.outbox[0]

    assert m.subject == 'WT login'
    assert m.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(m.to) == [EMAIL]
    assert 'https://localhost:8000/accounts/login/' in m.body

    mail.outbox = []


def test_login_token_view(test_user, client):
    context = create_link_context(test_user)
    url = reverse('login_token', kwargs={
        'uidb64': context['uid'], 'token': context['token']})

    assert test_user.last_login is None
    response = client.get(url)

    test_user.refresh_from_db()
    assert response.status_code == 302
    assert test_user.last_login


def test_login_token_view_fail(test_user, client):
    url = reverse('login_token', kwargs={'uidb64': 'MX', 'token': 'token'})

    response = client.get(url)

    assert response.status_code == 403


def test_login_view(test_user, client, caplog):
    url = reverse('login_form')
    response = client.get(url)

    assert 'form' in response.context
    assert response.status_code == 200

    # wrong email
    response = client.post(url, {'email': 'bad@email.cz'})

    assert response.status_code == 200
    assert response.context['form'].errors == {'email': ['No such account, please register first']}
    assert caplog.record_tuples == [
        ('accounts.forms', 30, 'Attempt to login with non-existent email bad@email.cz')
    ]
    caplog.clear()

    # ok email
    response = client.post(url, {'email': test_user.email})

    assert response.status_code == 302
    assert caplog.record_tuples == [
        ('accounts.views', 10, 'Sending email to tester@test.cz')
    ]
    assert len(mail.outbox) == 1

    mail.outbox = []


@pytest.mark.django_db
def test_registration_view(client, caplog, monkeypatch):
    url = reverse('register')

    response = client.get(url)

    assert 'form' in response.context
    assert response.status_code == 200

    # don't validate the reCAPTCHA
    monkeypatch.setattr('accounts.forms.RegistrationForm.clean_g_recaptcha_response',
                        lambda x: True)

    # wrong email
    response = client.post(url, {'email': 'bad@email'})
    assert response.status_code == 200
    assert response.context['form'].errors

    # ok email
    response = client.post(url, {'email': 'new@email.cz'})

    assert response.status_code == 302
    assert caplog.record_tuples == [
        ('accounts.views', 10, 'Registering new user new@email.cz'),
        ('accounts.views', 10, 'Sending email to new@email.cz')
    ]
    assert len(mail.outbox) == 1

    mail.outbox = []


@pytest.mark.django_db
def test_profile_view(client, admin_client):
    url = reverse('profile')
    response = client.get(url)

    assert response.status_code == 302
    assert response['Location'] == '/accounts/login/?next=/accounts/profile/'

    # logged in user
    response = admin_client.get(url)

    assert response.status_code == 200
    assert 'form' in response.context

    response = admin_client.post(url, {'first_name': 'Jerry',
                                       'eth_address': '0x4a4ac8d0b6a2f296c155c15c2bcaf04641818b78'})

    user = User.objects.get(username='admin')
    assert response.status_code == 302
    assert user.first_name == 'Jerry'
    assert user.eth_address == 'fapfapfap'


@pytest.mark.django_db
def test_logout_view_get(client, admin_client):
    url = reverse('logout')
    response = client.get(url)

    # not logged in can't visit
    assert response.status_code == 302
    assert response['Location'] == '/accounts/login/?next=/accounts/logout/'

    # logged in user
    response = admin_client.get(url)

    assert response.status_code == 302
    assert response['Location'] == '/accounts/login/'


@pytest.mark.django_db
def test_logout_view_post(admin_client):
    url = reverse('logout')
    response = admin_client.post(url)

    assert response.status_code == 302
    assert response['Location'] == '/accounts/login/'


def test_onfido_create_applicant(onfido_test_user):
    result = onfido_api.create_applicant(onfido_test_user)
    assert result.to_dict() == {
        'addresses': [{'building_name': None, 'id': None, 'town': 'London', 'flat_number': None,
                       'postcode': 'SW4 6EH', 'start_date': None, 'street': 'Main Street',
                       'state': None, 'country': 'GBR', 'building_number': '100', 'end_date': None,
                       'sub_street': None}],
        'country': 'gbr',
        'country_of_birth': None,
        'created_at': everything_equals,
        'dob': date(1980, 1, 1),
        'email': 'tester@test.cz',
        'first_name': 'Caligula',
        'gender': None,
        'href': everything_equals,  # '/v2/applicants/294da182-2431-4d74-ad2b-c35e94ce7dbf',
        'id': everything_equals,  # '294da182-2431-4d74-ad2b-c35e94ce7dbf',
        'id_numbers': [],
        'last_name': 'Tesla',
        'middle_name': None,
        'mobile': '+420777619338',
        'mothers_maiden_name': None,
        'nationality': None,
        'previous_last_name': None,
        'sandbox': True,
        'telephone': None,
        'title': None,
        'town_of_birth': None}


def test_onfido_create_applicant_handle_err(onfido_test_user):
    onfido_test_user.postcode = '111'
    with pytest.raises(ValidationError) as e:
        onfido_api.create_applicant(onfido_test_user)
    assert e.value.message == "There was a validation error on this request " \
                              "{'addresses': [{'postcode': ['invalid postcode']}]}"



def test_onfido_check(onfido_test_user):
    applicant = onfido_api.create_applicant(onfido_test_user)
    check_result = onfido_api.check(applicant.id)
    assert check_result.to_dict() == {
        'created_at': everything_equals,
        'download_uri': everything_equals,
        # 'https://onfido.com/dashboard/pdf/information_requests/8078549'
        'form_uri': everything_equals,
        # 'https://onfido.com/information/d5a121b3-f81c-4509-85cb-e092b719332c',
        'href': everything_equals,
        # '/v2/applicants/876e88c7-fa28-4134-b550-ace6497c9eb4/checks/d5a121b3-f81c-4509-85cb-e092b719332c',
        'id': everything_equals,  # 'd5a121b3-f81c-4509-85cb-e092b719332c',
        'redirect_uri': None,
        'reports': [{'breakdown': {},
                     'created_at': everything_equals,
                     'href': everything_equals,  #'/v2/checks/a80ca04e-ffe4-4a6f-b18f-4a7219f1106b/reports/6595886f-2554-4cc2-998d-ba5c7334f1f8',
                     'id': everything_equals,  #'6595886f-2554-4cc2-998d-ba5c7334f1f8',
                     'name': 'document',
                     'properties': {},
                     'result': None,
                     'status': 'awaiting_data',
                     'sub_result': None,
                     'variant': 'standard'},
                    {'breakdown': {},
                     'created_at': everything_equals,  # '2018-01-24T09:39:57Z',
                     'href': everything_equals,
                     # '/v2/checks/d5a121b3-f81c-4509-85cb-e092b719332c/reports/a77327a7-04f0-45af-991f-b620e394c942',
                     'id': everything_equals,  # 'a77327a7-04f0-45af-991f-b620e394c942',
                     'name': 'identity',
                     'properties': {},
                     'result': None,
                     'status': 'awaiting_data',
                     'sub_result': None,
                     'variant': 'standard'}],
        'result': None,
        'results_uri': everything_equals,
        # 'https://onfido.com/dashboard/information_requests/8078549',
        'status': 'awaiting_applicant',
        'tags': [],
        'type': 'standard'
    }


def test_onfido_check_reload(onfido_test_user):
    applicant = onfido_api.create_applicant(onfido_test_user)
    check_result = onfido_api.check(applicant.id)
    reload_check_result = onfido_api.check_reload(applicant.id, check_result.id)
    # pprint(check_result)
    assert reload_check_result.to_dict() == {
        'created_at': everything_equals,
        'download_uri': everything_equals,
        # 'https://onfido.com/dashboard/pdf/information_requests/8078952',
        'form_uri': everything_equals,
        # 'https://onfido.com/information/44d63663-1449-4623-883b-a549d3eeab9d',
        'href': everything_equals,
        # '/v2/applicants/c52662b7-808f-4422-98ca-816df8593b08/checks/44d63663-1449-4623-883b-a549d3eeab9d',
        'id': everything_equals,  # '44d63663-1449-4623-883b-a549d3eeab9d',
        'redirect_uri': None,
        'reports': [everything_equals, everything_equals],
        'result': None,
        'results_uri': everything_equals,
        # 'https://onfido.com/dashboard/information_requests/8078952',
        'status': 'awaiting_applicant',
        'tags': [],
        'type': 'standard'}


def test_test_onfido_check_model(onfido_test_user):
    check = onfido_test_user.onfido_check()
    onfidos = list(onfido_test_user.onfidos.all())
    assert len(onfidos) == 2
    applicant_model = onfidos[1]
    assert applicant_model.applicant_id
    assert applicant_model.type == 'applicant'
    assert applicant_model.response
    assert applicant_model.result == ''

    assert check.applicant_id
    assert check.type == 'check'
    assert check.response
    assert check.result == ''
    assert check.status == 'awaiting_applicant'

    # test reload
    reload = onfido_test_user.last_check.check_reload()
    onfidos = list(onfido_test_user.onfidos.all())
    assert len(onfidos) == 3
    assert reload.id == onfidos[0].id
    assert check.applicant_id == reload.applicant_id
    assert reload.type == 'check'
    assert reload.response
    assert reload.result == ''
    assert reload.status == 'awaiting_applicant'


def test_onfido_webhook(client, test_user):
    url = reverse('onfido_webhook')
    OnfidoCall.objects.create(onfido_id='b9bc1173-fd77-403e-af99-a07e476a5214', applicant_id='apld',
                              user=test_user, type='check')
    response = client.post(url,
                           data="""{"payload":{"action":"check.completed","resource_type":"check","object":{"completed_at":"2018-01-27 18:16:44 UTC","href":"https://api.onfido.com/v2/applicants/0f449cf6-3ac1-490e-866c-810f4cd34dd8/checks/36ce8df1-9af0-41e5-a6f9-6c6639210680","id":"36ce8df1-9af0-41e5-a6f9-6c6639210680","status":"complete"}}}""",
                           content_type='application/json',
                           **{'X-SIGNATURE': '2fd29c40d8891055fb6bbc3c45d77436aced0897'})
    assert response.status_code == 200
    assert response.content == b'OK'

    m = mail.outbox[0]

    assert m.subject == 'WT verification status'
    assert m.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(m.to) == [EMAIL]
    assert 'http://localhost:8000/accounts/login/' in m.body

    mail.outbox = []


def test_eth_get_total():
    transactions = get_transactions()
    total = eth_get_total(transactions)
    print(total / (10 ** 18))
    assert total == 2576817159433516273420


def test_get_sum_for_accounts():
    accounts = ['0x67ee267ff3c58d4248ff4ab2a0d44ee1b9289d69',
                '0x1d64480c8ae05e25169274022987e7089921302a']
    transactions = get_transactions()
    sums = get_sum_for_accounts(transactions, accounts)
    assert sums == {'0x1d64480c8ae05e25169274022987e7089921302a': 2000000000000000000,
                    '0x67ee267ff3c58d4248ff4ab2a0d44ee1b9289d69': 1000000000000000000}
