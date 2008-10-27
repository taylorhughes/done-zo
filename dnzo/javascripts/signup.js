var Signup = {
  CHECK_DELAY: 500, // milliseconds
  
  onKeyDown: function(event)
  {
    if (Signup.checking)
    {
      clearTimeout(Signup.checking);
    }
    Signup.checking = setTimeout(Signup.check,Signup.CHECK_DELAY);
  },
  
  check: function(event)
  {
    var current = $F(Signup.nameField);
    if (!Signup.lastChecked || Signup.lastChecked != current)
    {
      Signup.lastChecked = current;
      new Ajax.Request(Signup.availabilityURL, {
        method: 'get',
        parameters: {
          'name': current
        },
        onSuccess: Signup.doCheck
      });
    }
  },
  
  doCheck: function(xhr)
  {
    Signup.availabilityHolder.innerHTML = xhr.responseText;
  },
  
  load: function(event)
  {
    Signup.nameField = $('name');
    Signup.availabilityURL = $('availability').href;
    Signup.availabilityHolder = $('availability_holder');
    Event.observe(Signup.nameField,'keydown',Signup.onKeyDown);
  }
}

Event.observe(window, 'load', Signup.load);