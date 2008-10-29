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
    var avail = $('availability');
    var parent = avail.parentNode;
    var temp = new Element('div');
    temp.innerHTML = xhr.responseText;

    Signup.replaceElement(parent,temp,'availability');
    Signup.replaceElement(parent,temp,'unavailable_message');
  },
  
  // Replaces an element in parent with an element in temp
  // with a certain ID.
  replaceElement: function(parent, temp, id)
  {
    var elementById = function(p,cid)
    {
      var r = p.select("#" + cid);
      if (r.length > 0) return r[0];
      return null;
    }
    var newElement = elementById(temp,id);
    var existingElement = elementById(parent,id);
  
    if (newElement && existingElement)
    {
      parent.insertBefore(newElement,existingElement);
      parent.removeChild(existingElement);
    }
    else if (newElement)
    {
      parent.appendChild(newElement);
    }
    else if (existingElement)
    {
      parent.removeChild(existingElement);
    }
  },
  
  load: function(event)
  {
    Signup.nameField = $('name');
    Signup.availabilityURL = $('availability').href;
    Event.observe(Signup.nameField,'keydown',Signup.onKeyDown);
  }
}

Event.observe(window, 'load', Signup.load);