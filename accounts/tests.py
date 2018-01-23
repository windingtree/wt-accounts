# Create your tests here.
from unittest.mock import Mock

import pytest
from datetime import date
from django.core import mail
from django.forms import model_to_dict
from django.urls import reverse

from accounts import onfido_api
from accounts.forms import RegistrationForm
from accounts.models import create_link_context, send_login_email, User

EMAIL = 'tester@test.cz'

# will be equal to everything, usefull for ids and dates
everything_equals = type('omnieq', (), {"__eq__": lambda x, y: True})()


# TODO test confusable stuff a bit

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username=EMAIL, email=EMAIL)


@pytest.fixture
def onfido_test_user(db):
    user = User.objects.create_user(username=EMAIL, email=EMAIL)
    user.first_name = 'Nikola'
    user.last_name = 'Tesla'
    user.birth_date = date(1980, 1, 1)
    user.building_number = '100'
    user.street = 'Main Street'
    user.town = 'London'
    user.postcode = 'SW4 6EH'
    user.country = 'GBR'
    return user


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
    assert response.status_code == 302

    assert caplog.record_tuples == [
        ('accounts.views', 30, 'Attempt to login with non-existent email bad@email.cz')
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

    response = admin_client.post(url, {'street': 'over the rainbow', 'eth_address': 'fapfapfap'})

    user = User.objects.get(username='admin')
    assert response.status_code == 302
    assert user.street == 'over the rainbow'
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
        'addresses': [{'building_name': None,
                       'building_number': '100',
                       'country': 'GBR',
                       'end_date': None,
                       'flat_number': None,
                       'id': None,
                       'postcode': 'SW4 6EH',
                       'start_date': None,
                       'state': None,
                       'street': 'Main Street',
                       'sub_street': None,
                       'town': 'London'}],
        'country': 'gbr',
        'country_of_birth': None,
        'created_at': everything_equals,
        'dob': date(1980, 1, 1),
        'email': 'tester@test.cz',
        'first_name': 'Nikola',
        'gender': None,
        'href': everything_equals,
        'id': everything_equals,
        'id_numbers': [],
        'last_name': 'Tesla',
        'middle_name': None,
        'mobile': None,
        'mothers_maiden_name': None,
        'nationality': None,
        'previous_last_name': None,
        'sandbox': True,
        'telephone': None,
        'title': None,
        'town_of_birth': None
    }


def test_onfido_check(onfido_test_user):
    applicant = onfido_api.create_applicant(onfido_test_user)
    check_result = onfido_api.check(applicant.id)
    assert check_result.to_dict() == {
        'created_at': everything_equals,
        'download_uri': everything_equals,
        # 'https://onfido.com/dashboard/pdf/information_requests/8033882',
        'form_uri': None,
        'href': everything_equals,
        # '/v2/applicants/024fd02c-8b01-4ac9-9a9c-e5e9b6bae8e4/checks/63357bde-f5b8-435e-b77f-d3dc0d6d3f9b',
        'id': everything_equals,
        'redirect_uri': None,
        'reports': [
            {'breakdown': {
                'address': {
                    'breakdown': {
                        'credit_agencies': {'properties': {'number_of_credit_agencies': '1'},
                                            'result': 'clear'},
                        'telephone_database': {'properties': {}, 'result': 'clear'},
                        'voting_register': {'properties': {}, 'result': 'clear'}},
                    'result': 'clear'},
                'date_of_birth': {
                    'breakdown': {'credit_agencies': {'properties': {}, 'result': 'clear'},
                                  'voting_register': {'properties': {}, 'result': 'clear'}},
                    'result': 'clear'},
                'mortality': {'result': None}},
                'created_at': everything_equals,
                'href': everything_equals,
                # '/v2/checks/63357bde-f5b8-435e-b77f-d3dc0d6d3f9b/reports/e1d09b30-ff66-4b5e-be6c-1763040d4da1',
                'id': everything_equals,
                'name': 'identity',
                'properties': {
                    'matched_address': everything_equals,  # 4281266,
                    'matched_addresses': [
                        {'id': everything_equals,
                         'match_types': ['credit_agencies', 'voting_register']}]},
                'result': 'clear',
                'status': 'complete',
                'sub_result': None,
                'variant': 'standard'}],
        'result': 'clear',
        'results_uri': everything_equals,
        # 'https://onfido.com/dashboard/information_requests/8033882',
        'status': 'complete',
        'tags': [],
        'type': 'express'
    }


def test_test_onfido_check_model(onfido_test_user):
    assert onfido_test_user.onfido_check() is None
    onfidos = list(onfido_test_user.onfidos.all())
    assert len(onfidos) == 2
    applicant_model = onfidos[0]
    assert applicant_model.type == 'applicant'
    assert applicant_model.response
    assert applicant_model.result == ''

    check_model = onfidos[1]
    assert check_model.type == 'check'
    assert check_model.response
    assert check_model.result == 'clear'
