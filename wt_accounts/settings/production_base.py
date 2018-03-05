from .base import *

replace_in_production = '<replace in production>'

DEBUG = False

# https://lif.windingtree.com/
DOMAIN = 'lif.windingtree.com'
ALLOWED_HOSTS = [
    'wt-accounts-2096655128.ap-northeast-1.elb.amazonaws.com', # elb
    'lif.windingtree.com',
]

# security
SESSION_COOKIE_SECURE = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'wt',
        'USER': 'wt',
        'PASSWORD': replace_in_production,
        'HOST': 'wt-accounts.cvlintg75rfu.ap-northeast-1.rds.amazonaws.com',
        'OPTIONS': {'charset': 'utf8'},
    }
}

# recaptcha
RECAPTCHA_SITE_KEY = '6Ld090IUAAAAAHZZuWyteUJcLGZRBgUgOlQGspjO'
RECAPTCHA_SITE_SECRET = replace_in_production

import raven
RAVEN_CONFIG = {
    'dsn': replace_in_production, 
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(BASE_DIR),
}

# mailing
EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
MAILGUN_ACCESS_KEY = replace_in_production
MAILGUN_SERVER_NAME = 'mg.windingtree.com'

# static files
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.CachedStaticFilesStorage"

# smtp settings - because mailgun failed us
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = '587'
EMAIL_HOST_USER = 'walksource'
EMAIL_HOST_PASSWORD = 't)RnnQUY?e3i^Gon3zG7iY7cfy)eYR'
EMAIL_USE_TLS = True

EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
SENDGRID_API_KEY = replace_in_production
SENDGRID_SANDBOX_MODE_IN_DEBUG = False

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'wt_cache_table',
    }
}

ONFIDO_TOKEN = replace_in_production
ONFIDO_WEBHOOK_TOKEN = replace_in_production

AWS_ACCESS_KEY_ID = "AKIAJHHI3JSHVUXA4JTQ"
AWS_SECRET_ACCESS_KEY = replace_in_production
AWS_S3_BUCKET_NAME = "files.lif.windingtree.com"

