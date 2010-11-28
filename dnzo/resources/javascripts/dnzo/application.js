DNZO = Object.extend(DNZO, {
  // Designate the status of a XHR response
  RESPONSE_STATUS: {
    INTERRUPTED: 'TASK_RESPONSE_INTERRUPTED',
    LOGGED_OUT: 'TASK_RESPONSE_LOGGED_OUT',
    ERROR: 'TASK_RESPONSE_ERROR',
    SUCCESS: 'TASK_RESPONSE_SUCCESS'
  },
  
  HIDE_STATUS_DELAY: 15, // seconds
  
  load: function(event)
  {
    // Setup dropdown switcher
    var switcher = $('switcher');
    
    if (switcher)
    {
      switcher.enable();
      switcher.observe('change', DNZO.onSwitchList); 
    }
    
    $$('a.dialog').each(function(dialogLink) {
      new ModalDialog.Ajax(dialogLink);
    });
    
    DNZO.setHideStatus();
    DNZO.verifyTimezone();
    DNZO.setupLoggedOutDetect();
  },
  
  strcmp: function(a,b)
  {
    a = a.toLowerCase();
    b = b.toLowerCase();
  
    if (a==b) { return 0; }
    return a < b ? -1 : 1;
  },
  
  onSwitchList: function(event)
  {
    var switcher = event.element();
    switcher.disable();
    document.location.href = $F(switcher);
  },
  
  verifyTimezone: function()
  {
    if (DNZO.timezoneInfo.updateUrl.length == 0) { return; }
    
    var currentOffset = (new Date()).getTimezoneOffset();
    if (DNZO.timezoneInfo.offset != currentOffset)
    {
      new Ajax.Request(DNZO.timezoneInfo.updateUrl, {
        parameters: { offset: currentOffset },
        method: 'post'
      });
    }
  },
  
  getResponseStatus: function(xhr)
  {
    var response = DNZO.RESPONSE_STATUS.SUCCESS;
    
    if (!xhr.status)
    {
      response = DNZO.RESPONSE_STATUS.INTERRUPTED;
    } 
    else if (xhr.status == 200)
    {
      if (!xhr.responseText || xhr.responseText.indexOf('task-ajax-response') < 0)
      {
        response = DNZO.RESPONSE_STATUS.LOGGED_OUT;
      }
    }
    else if (xhr.status == 302)
    {
      response = DNZO.RESPONSE_STATUS.LOGGED_OUT;
    }
    else
    {
      response = DNZO.RESPONSE_STATUS.ERROR;
    }
    
    return response;
  },
  
  LOGOUT_DETECT_INTERVAL: 180, // seconds

  setupLoggedOutDetect: function()
  {
    // Don't check right after page load.
    DNZO.lastLogoutCheck = new Date().getTime();
    Element.observe(document, 'mousemove', function(event) {
      // Check on mouse move only after interval seconds
      DNZO.maybeDetectLogout(false);
    });
    Element.observe(window, 'focus', function(event) {
      // When we refocus on the window, always check
      DNZO.maybeDetectLogout(event.target == window);
    });
  },

  maybeDetectLogout: function(opt_force) {  
    // Check every minute while the mouse is moving around
    var time = new Date().getTime();
    var timeSince = time - DNZO.lastLogoutCheck;
    var interval = DNZO.LOGOUT_DETECT_INTERVAL * 1000;
    if (opt_force || timeSince > interval) {
      DNZO.lastLogoutCheck = time;
      DNZO.detectLogout(opt_force);
    }
  },
  
  detectLogout: function(wasForced)
  {
    if (!DNZO.noopUrl) { return; }

    var params = {};
    if (wasForced) {
      params['forced'] = true;
    }

    new Ajax.Request(DNZO.noopUrl, {
      method: 'get',
      parameters: params,
      onComplete: function(xhr) {
        if (DNZO.getResponseStatus(xhr) == DNZO.RESPONSE_STATUS.LOGGED_OUT) {
          DNZO.showStatus(DNZO.Messages.LOGGED_OUT_STATUS);
        }
      }
    });
  },
  
  setHideStatus: function()
  {
    if (DNZO.hideStatusTimeout)
    {
      clearTimeout(DNZO.hideStatusTimeout);
    }
    DNZO.hideStatusTimeout = setTimeout(DNZO.hideStatus, DNZO.HIDE_STATUS_DELAY * 1000);
  },
  
  hideStatus: function()
  {
    var status = $('status');
    if (!status) { return; }
    
    var subeffects = status.immediateDescendants().collect(function(child){
      return new Effect.Fade(child, { sync: true });
    });
    
    new Effect.Parallel(subeffects, {
      duration: 0.1,
      afterFinish: function() {
        new Effect.BlindUp(status, { duration: 0.1 });
      }
    });
  },
  
  showStatus: function(messageHTML)
  {
    var status = $('status');

    if (!status)
    {
      status = new Element('div', {'id': 'status'});
      status.hide();
      $('body').appendChild(status);
    }
    
    status.innerHTML = messageHTML;
    
    if (status.visible())
    {
      // Already visible, just highlight that it's a new status
      new Effect.Highlight(status, { duration: 0.2 });
      return;
    }
    
    var subeffects = status.immediateDescendants().collect(function(child){
      child.hide();
      return new Effect.Appear(child, { sync: true });
    });
    
    new Effect.BlindDown(status, { 
      duration: 0.1,
      afterFinish: function() {
        new Effect.Parallel(subeffects, { duration: 0.1 });
      }
    });
  },
  
  containerFromResponse: function(xhr)
  {
    var temp = new Element('div');
    temp.innerHTML = xhr.responseText;
    return temp;
  },
  
  updateStatusFromResponse: function(xhr)
  {
    var container = DNZO.containerFromResponse(xhr);
    status = container.select("div").find(function(div){
      return div.id == "status";
    });
    
    if (!status)
    {
      return;
    }
    
    DNZO.showStatus(status.innerHTML);
    DNZO.setHideStatus();
  }
});

Event.observe(window,'load',DNZO.load);
