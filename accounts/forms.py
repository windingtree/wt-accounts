# -*- coding: utf-8 -*-
import logging

import requests
from django import forms
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.utils.translation import ugettext_lazy as _

from accounts import validators
from accounts.models import User

logger = logging.getLogger(__name__)


class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        help_text=_(u'email address'),
        required=True,
        validators=[
            validators.validate_confusables_email,
        ]
    )

    g_recaptcha_response = forms.CharField(required=False)
    terms_accepted = forms.BooleanField(label=_('I accept the <a href="%sToken Sale T&Cs.pdf">'
                                                'Terms and Conditions</a>') % settings.STATIC_URL,
                                        error_messages={'required': validators.TOS_REQUIRED}
                                        )
    non_us_resident = forms.BooleanField(label=_('I am not a US resident'))

    class Meta:
        model = User
        fields = ('email',)
        required_css_class = 'required'

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the site.
        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(validators.DUPLICATE_EMAIL)
        return self.cleaned_data['email'].lower()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.set_unusable_password()
        if commit:
            user.save()
        return user

    def clean_g_recaptcha_response(self):
        """
        the actual value comes from `g-recaptcha-response` which I'm unable to get
        easily from form.
        """

        g_recaptcha_response = self.data.get('g-recaptcha-response')
        if g_recaptcha_response in EMPTY_VALUES:
            raise forms.ValidationError('reCAPTCHA required')

        r = requests.post('https://www.google.com/recaptcha/api/siteverify', {
            'secret': settings.RECAPTCHA_SITE_SECRET,
            'response': g_recaptcha_response,
        })
        r = r.json()
        if not r['success']:
            raise forms.ValidationError('reCAPTCHA - {}'.format(r['error-codes']))
        return g_recaptcha_response


class LoginForm(forms.Form):
    email = forms.EmailField(
        help_text=_(u'email address'),
        widget=forms.TextInput(attrs={'autofocus': True}),
    )

    def clean_email(self):
        value = self.cleaned_data['email']
        if not User.objects.filter(email=value).exists():
            logger.warning('Attempt to login with non-existent email %s', value)
            raise forms.ValidationError('No such account, please register first')
        return value

    @property
    def user(self):
        try:
            return User.objects.get(email=self.cleaned_data['email'])
        except User.DoesNotExist:
            return None


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'birth_date', 'mobile', 'street', 'building_number',
            'town', 'postcode', 'country', 'eth_address', 'proof_of_address_file')
        required_css_class = 'required'


class VerifyForm(forms.Form):

    def __init__(self, *args, user, **kwargs):
        self.user = user
        self.onfido_check = None
        super().__init__(*args, **kwargs)

    def clean(self):
        super(VerifyForm, self).clean()
        self.onfido_check = self.user.onfido_check()
        return self.cleaned_data
