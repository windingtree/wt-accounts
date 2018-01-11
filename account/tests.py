# Create your tests here.

import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.forms import model_to_dict
from django.urls import reverse

from account.forms import RegistrationForm
from account.models import create_link_context, send_login_email

EMAIL = 'tester@test.cz'


# TODO test confusable stuff a bit

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username=EMAIL, email=EMAIL)


@pytest.mark.django_db
def test_RegistrationForm():
    form = RegistrationForm()
    assert form.is_valid() == False

    form = RegistrationForm(data={'email': EMAIL})
    assert form.is_valid()

    user = form.save()
    user_data = model_to_dict(user)

    assert user_data.pop('password').startswith('!')
    assert user_data.pop('date_joined')
    assert user_data == {
        'email': 'tester@test.cz',
        'first_name': '',
        'groups': [],
        'id': 1,
        'is_active': True,
        'is_staff': False,
        'is_superuser': False,
        'last_login': None,
        'last_name': '',
        'user_permissions': [],
        'username': 'tester@test.cz'
    }


def test_create_link_context(test_user):
    context = create_link_context(test_user)
    assert len(context.pop('token')) == 24
    assert context == {
        'domain': 'www.wt.com',
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
    assert 'https://www.wt.com/account/login/' in m.body

    mail.outbox = []


def test_login_token_view(test_user, client):
    context = create_link_context(test_user)
    url = reverse('login_token', kwargs={
        'uidb64': context['uid'], 'token': context['token']})

    response = client.get(url)

    assert response.status_code == 302


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
        ('account.views', 30, 'Attempt to login with non-existent email bad@email.cz')
    ]
    caplog.clear()

    # ok email
    response = client.post(url, {'email': test_user.email})

    assert response.status_code == 302
    assert caplog.record_tuples == [
        ('account.views', 10, 'Sending email to tester@test.cz')
    ]
    assert len(mail.outbox) == 1

    mail.outbox = []


@pytest.mark.django_db
def test_registration_view(client, caplog):
    url = reverse('registration')
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
        ('account.views', 10, 'Registering new user new@email.cz'),
        ('account.views', 10, 'Sending email to new@email.cz')
    ]
    assert len(mail.outbox) == 1

    mail.outbox = []
