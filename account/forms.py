# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from account import validators


class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        help_text=_(u'email address'),
        required=True,
        validators=[
            validators.validate_confusables_email,
        ]
    )

    # tos = forms.BooleanField(
    #     widget=forms.CheckboxInput,
    #     label=_(u'I have read and agree to the Terms of Service'),
    #     error_messages={
    #         'required': validators.TOS_REQUIRED,
    #     }
    # )

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
        return self.cleaned_data['email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.set_unusable_password()
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        help_text=_(u'email address'),
        widget=forms.TextInput(attrs={'autofocus': True}),
    )

    @property
    def user(self):
        try:
            return User.objects.get(email=self.cleaned_data['email'])
        except User.DoesNotExist:
            return None
