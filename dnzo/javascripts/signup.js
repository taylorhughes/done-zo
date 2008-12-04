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
    // Replace the image
    var newAvail = Signup.elementFromText(xhr,'a');
    var avail = $('availability');
    var parent = avail.parentNode;

    parent.insertBefore(newAvail,avail);
    parent.removeChild(avail);
    
    // Replace or insert the message
    var newMessage = Signup.elementFromText(xhr,'p');
    var message = $('unavailable_message');
    // The message goes above buttons
    var buttons = $('buttons');
    parent = buttons.parentNode;
    
    if (message) parent.removeChild(message);
    parent.insertBefore(newMessage,buttons);
  },

  // Given an XHR, creates a temp element from the response and  
  // extracts an element with a given id from within it.
  elementFromText: function(xhr,selector)
  {
    var temp = new Element('div');
    temp.innerHTML = xhr.responseText;
    var r = temp.select(selector);
    if (r.length > 0) 
    {
      return r[0];
    }
    return null;
  },
  
  load: function(event)
  {
    Signup.nameField = $('name');
    Signup.availabilityURL = $('availability').href;
    Signup.nameField.observe('keydown',Signup.onKeyDown);
  }
}

Event.observe(window, 'load', Signup.load);