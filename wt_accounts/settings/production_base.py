from .base import *

DEBUG = False

# https://lif.windingtree.com/
DOMAIN = 'lif.windingtree.com'
ALLOWED_HOSTS = [
    'wt-accounts-2096655128.ap-northeast-1.elb.amazonaws.com', # elb
    'lif.windingtree.com',
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

