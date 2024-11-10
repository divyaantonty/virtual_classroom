import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-k=ah64yxejvl%6*uih0nscqb5_v-bwod7+e7s+4^83^e1dv05+'
DEBUG = True
ALLOWED_HOSTS = ['*']

RAZORPAY_API_KEY = 'rzp_test_o8cawEIEiGsQ6C'
RAZORPAY_API_SECRET = 'ITd8ronAQbSCUCqvlqkMlxYl'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myApp',
    
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware'

]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

# DATABASES = {
#   'default': {
#        'ENGINE': 'django.db.backends.mysql',
#        'NAME': 'vc1',  
#        'USER': 'root',    
#        'PASSWORD': '',  
#        'HOST': 'localhost',
#        'PORT': '3306',
#     }
#  }

# settings.py

DATABASES = {
   'default': {
      'ENGINE': 'django.db.backends.mysql',
      'USER': 'vc_signcalmso',
      'NAME':'vc_signcalmso',
       'PASSWORD': 'c71dc785d3e6c51ca733e9fef1c71f56a20afd30',  # Replace with your actual password
       'HOST': '5v7yf.h.filess.io',
       'PORT': '3307',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'myApp', 'static')]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'myApp.CustomUser' 
LOGIN_URL = '/login/' 


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'divyaantony2025@mca.ajce.in'
EMAIL_HOST_PASSWORD = 'Ajce2025' 
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

