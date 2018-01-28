from .base import *

DEBUG = False

ALLOWED_HOST = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'wt',
        'USER': 'wt',
        'PASSWORD': '',
        'HOST': 'wt-accounts.cvlintg75rfu.ap-northeast-1.rds.amazonaws.com',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

