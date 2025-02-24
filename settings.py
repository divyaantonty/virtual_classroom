MIDDLEWARE = [
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ... other middleware
]

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('ar', 'Arabic'),
    ('hi', 'Hindi'),
    ('fr', 'French'),
    # Add more languages as needed
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

LANGUAGE_CODE = 'en'

USE_I18N = True
USE_L10N = True

CSRF_COOKIE_SECURE = False  # Set to True in production
CSRF_COOKIE_HTTPONLY = False 

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 