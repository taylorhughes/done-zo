import environment

DEBUG          = environment.IS_DEVELOPMENT
TEMPLATE_DEBUG = environment.IS_DEVELOPMENT

DATABASE_ENGINE = 'appengine'

USE_I18N = False

TEMPLATE_LOADERS = (
  # Load basic template files in the normal way
  'django.template.loaders.filesystem.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('Taylor Hughes', 'taylor@taylor-hughes.com'),
)

MIDDLEWARE_CLASSES = (
  # does things like APPEND_SLASH for URLs
  'django.middleware.common.CommonMiddleware',
)

ROOT_URLCONF = 'urls'

import os
ROOT_PATH = os.path.dirname(__file__)
TEMPLATE_DIRS = (
  ROOT_PATH + '/resources/templates'
)

INSTALLED_APPS = (
  'tasks',
  'public',
  'admin',
)
