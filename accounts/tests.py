# Create your tests here.

import pytest
from django.core import mail
from django.forms import model_to_dict
from django.urls import reverse

from accounts.forms import RegistrationForm
from accounts.models import create_link_context, send_login_email, User

EMAIL = 'tester@test.cz'

# will be equal to everything, usefull for ids and dates
everything_equals = type('omnieq', (), {"__eq__": lambda x, y: True})()


# TODO test confusable stuff a bit

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username=EMAIL, email=EMAIL)


@pytest.mark.django_db
def test_RegistrationForm():
    form = RegistrationForm()
    assert form.is_valid() == False

    form = RegistrationForm(data={'email': EMAIL.upper()})
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
        'country': None,
        'postcode': '',
        'street': '',
        'town': '',
        'crypto_hash': '',
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
def test_registration_view(client, caplog):
    url = reverse('register')
    response = client.get(url)

    assert 'form' in response.context
    assert response.status_code == 200

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

    response = admin_client.post(url, {'street': 'over the rainbow', 'crypto_hash': 'fapfapfap'})

    user = User.objects.get(username='admin')
    assert response.status_code == 302
    assert user.street == 'over the rainbow'
    assert user.crypto_hash == 'fapfapfap'
