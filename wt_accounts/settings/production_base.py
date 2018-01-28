from .base import *

DEBUG = False

# http://ec2-54-178-125-223.ap-northeast-1.compute.amazonaws.com/
DOMAIN = 'ec2-54-178-125-223.ap-northeast-1.compute.amazonaws.com'
ALLOWED_HOSTS = [
    'ec2-54-178-125-223.ap-northeast-1.compute.amazonaws.com',
    'wt-accounts-2096655128.ap-northeast-1.elb.amazonaws.com',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'wt',
        'USER': 'wt',
        'PASSWORD': '<replace-in-production>',
        'HOST': 'wt-accounts.cvlintg75rfu.ap-northeast-1.rds.amazonaws.com',
        'OPTIONS': {'charset': 'utf8'},
    }
}

# will be replaced by mailgun
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = "jakub.vysoky@gmail.com"
EMAIL_HOST_PASSWORD = '<replace-in-production>'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# recaptcha
RECAPTCHA_SITE_KEY = '6Ld090IUAAAAAHZZuWyteUJcLGZRBgUgOlQGspjO'
RECAPTCHA_SITE_SECRET = ''

import raven
RAVEN_CONFIG = {
    'dsn': '',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(BASE_DIR),
}

# mailing
EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
MAILGUN_ACCESS_KEY = ''
MAILGUN_SERVER_NAME = 'mg.windingtree.com'

