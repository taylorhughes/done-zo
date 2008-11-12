#from django.db import models
from google.appengine.ext import db

class Invitation(db.Model):
  email_address = db.StringProperty()
  created_at    = db.DateTimeProperty(auto_now_add=True)
  registered_at = db.DateTimeProperty()
  user          = db.UserProperty()