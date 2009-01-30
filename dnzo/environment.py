import os

IS_DEVELOPMENT   = ('Dev' in os.getenv('SERVER_SOFTWARE'))
IS_PRODUCTION    = not IS_DEVELOPMENT

CURRENT_VERSION  = os.getenv('CURRENT_VERSION_ID')
MAJOR_VERSION    = CURRENT_VERSION.split('.')[0]