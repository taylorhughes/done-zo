import os

software = os.getenv('SERVER_SOFTWARE')
IS_DEVELOPMENT   = software and ('Dev' in software)
IS_PRODUCTION    = not IS_DEVELOPMENT

CURRENT_VERSION  = os.getenv('CURRENT_VERSION_ID')
MAJOR_VERSION    = (CURRENT_VERSION or "").split('.')[0]