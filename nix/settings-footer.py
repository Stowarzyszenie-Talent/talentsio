if DEBUG:
    TEMPLATES[0]['OPTIONS']['loaders'] = UNCACHED_TEMPLATE_LOADERS
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    }
else:
    # Cache compiled templates in production environment.
    TEMPLATES[0]['OPTIONS']['loaders'] = CACHED_TEMPLATE_LOADERS
    INSTALLED_APPS.remove('debug_toolbar')
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')

TEMPLATES[0]['APP_DIRS'] = False
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

from basic_settings import *
