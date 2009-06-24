import re

from datetime import datetime, timedelta, date
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
RE_SPLIT    = re.compile(r'[^a-z0-9]+', re.I)

def parse_month(month_string):
  for i in range(1,13):
    if date(2008, i, 1).strftime('%B')[0:3].lower() in month_string.lower():
      return i
  
  return None
  
def parse_datetime(date_string):
  """Turns a string like 2009-06-24 04:30:24.906035 into a datetime."""
  if not date_string or not isinstance(date_string, (str,unicode)):
    return None
    
  digits = [int(p) for p in re.findall(r'\d+', date_string)]
  try:
    date = datetime(*digits[:7])
    return date
  except:
    pass
    
  return None
  
def parse_date(date_string, offset_mins=0, output_utc=False):
  if not date_string:
    return None
    
  date_string = date_string.strip()
  if len(date_string) == 0:
    return None
  
  now   = datetime.utcnow() - timedelta(minutes=offset_mins)
  today = datetime(*now.timetuple()[0:3])
  
  value = None
    
  if RE_TODAY.match(date_string):
    value = today
    
  elif RE_TOMORROW.match(date_string):
    value = today + timedelta(days=1)
    
  elif RE_DAY.match(date_string):
    day = RE_DAY.match(date_string).groups()[0].lower()
    next_day = today + timedelta(days=1)
    while next_day.strftime("%a").lower() != day:
      next_day += timedelta(days=1)
    value = next_day
  
  else:
    parts = RE_SPLIT.split(date_string)
    digits = [int(p)    for p in parts if re.match(r'^\d+$', p)]
    words =  [p.lower() for p in parts if re.match(r'^[a-z]+$', p.lower())]
    parts = digits + words
    
    if (len(parts) == 2 or len(parts) == 3) and len(words) <= 1:
      m, d, y = None, None, None
      
      if words:
        m = parse_month(words.pop())
        
      while digits:
        max_d = max(digits)
        if max_d > 31 and not y:
          y = max_d
          digits.remove(y)
          continue
        elif max_d > 12 and not d:
          d = max_d
          digits.remove(d)
          continue

        break
    
      digits.reverse()
    
      if digits and not m:
        m = digits.pop()
      if digits and not d:
        d = digits.pop()
      if digits and not y:
        y = digits.pop()
    
      try:
        if y:
          if y < 100 and y > 50:
            y += 1900
          elif y <= 50:
            y += 2000
          elif y < 1950:
            y = None
            
        else:
          y = now.timetuple()[0]
          if datetime(y, m, d) < today:
            y += 1
      
        value = datetime(y, m, d)
      
      except:
        pass
      

  if value and output_utc:
    value += timedelta(minutes=offset_mins)
  
  return value
  
  