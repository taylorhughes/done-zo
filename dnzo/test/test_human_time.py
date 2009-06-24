import unittest

from datetime import date, datetime, timedelta
from util.human_time import parse_date, parse_datetime

class HumanTimeTestCase(unittest.TestCase):
  months = [
    ['jan', 'january', 'janu', 'JAN', 'January'],
    ['feb', 'february', 'FeB', 'February'],
    ['mar', 'march', 'March'], 
    ['apr', 'april', 'April'],
    ['may', "MAY"],
    ['jun', 'june', 'JUNE'],
    ['jul', 'july'],
    ['aug', 'august', "AUG"],
    ['sep', 'sept', 'september'],
    ['oct', 'october'],
    ['nov', 'november', "NOV"],
    ['dec', 'december'],
  ]
  
  days = (
    ('mon', 'monday', 'Monday', 'Mon'),
    ('tues', 'Tue', 'Tuesday', 'tuesday'),
    ('weds', 'wed', 'Wed', 'WED', 'Wednesday'),
    ('thu', 'thurs', 'thursday', 'Thurs', "Thursday"),
    ('fri', 'Friday', 'friday'),
    ('sat', 'saturday', 'Saturday', 'Sat'),
    ('sun', 'Sunday', 'SUN'),
  )
  
  today = datetime(*datetime.utcnow().timetuple()[0:3])
  
  def test_parse_datetime(self):
    no_goes = (
      "nothin here!",
      "02 04 2009", # 2009 is too big for a day
      "1203984019284102498",
      "",
      None
    )
    for no_go in no_goes:
      parsed = parse_datetime(no_go)
      self.assertEqual(None, parsed, "Should not have been able to parse %s as a date, but got %s." % (no_go, parsed) )
  
    goes = (
      ("2009 02 04", (2009,2,4)),
      ("1995 2 4 5:32:50.12", (1995, 2, 4, 5, 32, 50, 12)),
      (u"2009-06-24 05:17:55.370572", (2009,6,24,5,17,55,370572))
    )
    for go, gotuple in goes:
      parsed = parse_datetime(go)
      self.assertEqual(datetime(*gotuple), parsed, "Parsed representation should be equal; provided %s, got %s." % (go, parsed))
      
  
  def test_parse_date(self):
    def get_date(date_tuple):
      if len(date_tuple) == 3:
        return datetime(*date_tuple)
      elif len(date_tuple) == 2:
        m, d = date_tuple
        y = self.today.timetuple()[0]
        if datetime(y, m, d) < self.today:
          y += 1
        return datetime(y, m, d)
      return None

    should_parse = {
      '1 2 3':       (2003, 1, 2),
      '2 2 2':       (2002, 2, 2),
      '3 2 1':       (2001, 3, 2),
      '3 13 2000':   (2000, 3, 13),
      '13 12 2000':  (2000, 12, 13),
      '12 13 2004':  (2004, 12, 13),
      '12 30 2000':  (2000, 12, 30),
      'dec 30 2000': (2000, 12, 30),
      '30 dec 2000': (2000, 12, 30),
      '30 dec 1998': (1998, 12, 30),
      '30 dec 98':   (1998, 12, 30),
      '13 12':       (12, 13),
      '31 1':        (1, 31),
      '31 jan':      (1, 31),
      '28 feb':      (2, 28),
      '29 feb 2008': (2008, 2, 29),
      '29 1 29':     (2029, 1, 29),
      '29 1 75':     (1975, 1, 29),
    }
    
    months = reduce(lambda x, y: x + y, [zip([(i + 1)] * len(month_names), month_names) for (i, month_names) in enumerate(self.months)])
    
    for (i, month_name) in months:
      should_parse.update({
        "%s-1-2009"  % month_name : (2009, i, 1 ),
        " %s - 1 - 2009 "  % month_name : (2009, i, 1 ),
        " 12 %s 2005" % month_name : (2005, i, 12),
        "12 %s 02  "   % month_name : (2002, i, 12),
        "  12 %s 98"   % month_name : (1998, i, 12),
        "12 %s   9"    % month_name : (2009, i, 12),
        "2012/12/%s" % month_name : (2012, i, 12),
        "%s/1"       % month_name : (i, 1),
        "1 %s"       % month_name : (i, 1),
      })

    datef = '%B %d %Y'
    for k in should_parse:
      parsed = parse_date(k)
      correct = get_date(should_parse[k])
      self.assertEquals(correct, parsed, "'%s' should have been parsed as %s, but was %s!" % (k, correct.strftime(datef), parsed.strftime(datef)))

  def test_not_parsable(self):
    not_parsable = (
      '2000 2000 2000',
      'abc 1 2009',
      'poop a doop',
      'feb 31',
      'fe 28 2009', # fe is not a month
      # 
      'feb 29 2009', # not a leap year
      '31 31',
      '2 1 202',
      '2a2a2009',
    )
    for bad in not_parsable:
      parsed = parse_date(bad)
      parsed = parsed and parsed.strftime('%B %d %Y')
      self.assertEqual(None, parsed, "'%s' should NOT have been parsed, but it was %s!" % (bad, parsed))
      
      
  def test_special_days(self):
    for day in reduce(lambda x, y: x + y, self.days):
      parsed = parse_date(day)
      self.assert_(parsed > self.today, "Parsed day name ('%s') should be the next day of that day name, so it should be greater than today." % day)
      self.assert_(parsed <= self.today + timedelta(weeks=1), "Parsed day name ('%s') should be no farther than a week from today." % day)
        
    self.assertEqual(self.today, parse_date('today'))
    self.assertEqual(self.today, parse_date('  today  '))
    self.assertEqual(self.today + timedelta(days=1), parse_date('tomorrow'))
    self.assertEqual(self.today + timedelta(days=1), parse_date('tomorrow '))
    self.assertEqual(self.today + timedelta(days=1), parse_date('   tomorrow '))

      