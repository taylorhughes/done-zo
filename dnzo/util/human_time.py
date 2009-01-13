import re

from datetime import datetime, timedelta
import calendar

def get_sunday(offset_mins):
  now    = datetime.utcnow() - timedelta(minutes=offset_mins)
  sunday = datetime(*now.timetuple()[0:3])
  while sunday.weekday() != calendar.SUNDAY:
    sunday -= timedelta(days=1)
  return sunday

def get_this_week_range(offset_mins=0):
  sunday = get_sunday(offset_mins)
  return (sunday + timedelta(minutes=offset_mins), sunday + timedelta(days=7, minutes=offset_mins))
    
def get_last_week_range(offset_mins=0):
  sunday = get_sunday(offset_mins)
  return (sunday - timedelta(days=7) + timedelta(minutes=offset_mins), sunday + timedelta(minutes=offset_mins))
  
def get_today_range(offset_mins=0):
  now   = datetime.utcnow() - timedelta(minutes=offset_mins)
  today = datetime(*now.timetuple()[0:3])
  return (today + timedelta(minutes=offset_mins), today + timedelta(hours=24, minutes=offset_mins))
    
def get_yesterday_range(offset_mins=0):
  now   = datetime.utcnow() - timedelta(minutes=offset_mins)
  today = datetime(*now.timetuple()[0:3])
  return (today - timedelta(hours=24) + timedelta(minutes=offset_mins), today + timedelta(minutes=offset_mins))
  
HUMAN_RANGES = (
  {
    'name':  'This week',
    'slug':  'this-week',
    'range': get_this_week_range
  },
  {
    'name':  'Last week',
    'slug':  'last-week',
    'range': get_last_week_range
  },
  {
    'name':  'Today',
    'slug':  'today',
    'range': get_today_range
  },
  {
    'name':  'Yesterday',
    'slug':  'yesterday',
    'range': get_yesterday_range
  },
)


RE_TODAY    = re.compile(r'^today$', re.I)
RE_TOMORROW = re.compile(r'^tom{1,2}or{1,2}ow$', re.I)
RE_DAY      = re.compile(r'^(mon|tue|wed|thu|fri|sat|sun)\w*$', re.I)
RE_DATE     = re.compile(r'^(\d{1,2})\D+(\d{1,2})(?:\D+(\d{1,4}))?$')

def parse_date(date_string, offset_mins=0):
  if not date_string:
    return None
    
  date_string = date_string.strip()
  if len(date_string) == 0:
    return None
  
  now   = datetime.utcnow() - timedelta(minutes=offset_mins)
  today = datetime(*now.timetuple()[0:3])
  
  match = RE_DATE.match(date_string)
  if match:
    m, d, y = match.groups()
    m = int(m)
    d = int(d)
    if y:
      y = int(y)
      if y < 100:
        y += 2000
      elif y < 2000:
        y = None
        
    if not y:
      y = now.timetuple()[0]
      if datetime(y, m, d) < today:
        y += 1
      
    return datetime(y, m, d)
    
  if RE_TODAY.match(date_string):
    return today
    
  if RE_TOMORROW.match(date_string):
    return today + timedelta(days=1)
    
  match = RE_DAY.match(date_string)
  if match:
    day = match.groups()[0].lower()
    next_day = today + timedelta(days=1)
    while next_day.strftime("%a").lower() != day:
      next_day += timedelta(days=1)
    return next_day
  
  return None