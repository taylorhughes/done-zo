
import os.path
import logging

from django import template
from django.template.loader import add_to_builtins


ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


add_to_builtins('templating.templating')
add_to_builtins('templating.dnzo_templating')


TEMPLATE_LOADERS = (
  'django.template.loaders.filesystem.Loader',
  'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
  'django.contrib.auth.context_processors.auth',
  'django.core.context_processors.request',
  'cluster_project.webapp.context_processors.constants',
)

TEMPLATE_DIRS = (
  ROOT_PATH + '/resources/templates',
)
