/*
 *  ModalDialog
 *
 *  ModalDialog is a class that takes a link or form button and loads
 *  its target into a modal dialog window. Options are highly limited
 *  at this point. 
 *
 *  This class adds two elements to the DOM: a "blackout" element, 
 *  which hides the unclickable background in a light black; and the
 *  actual dialog container, whose contents become whatever is returned
 *  from the link provided.
 *
 *  Usage:
 *
 *    new ModalDialog($('link_id'), { afterShown: function() {} });
 * 
 *  Options:
 *
 *    afterShown: a function to call after the dialog is shown.
 *
 */
var ModalDialog = Class.create({
  initialize: function(content, options) 
  {
    this.options = options || {};
    
    this.createElements();
    this.updateContent(content);
  },
  
  createElements: function()
  {
    if (this.blackout) { this.blackout.remove(); }
    this.blackout = new Element('div');
    this.blackout.addClassName('blackout');
    this.blackout.setStyle({
      position: 'absolute',
      display:  'none',
      background: 'black'
    });
       
    if (this.container) { this.container.remove(); }
    this.container = new Element('div');
    this.container.addClassName('dialog_container');

    this.container.setStyle({
      position: 'absolute',
      display:  'none'
    });
    
    var body = $('body');
    body.appendChild(this.blackout);
    body.appendChild(this.container);
  },
  
  position: function()
  {    
    var dimensions = this.container.getDimensions();
    var scrolled   = document.viewport.getScrollOffsets();
    var viewport   = document.viewport.getDimensions();

    var top = (viewport.height / 4) - (dimensions.height / 4) + scrolled.top;
    var left = (viewport.width / 2) - (dimensions.width / 2) + scrolled.left;

    this.blackout.setStyle({
      top:    scrolled.top + 'px', 
      left:   scrolled.left + 'px',
      width:  '100%',
      height: '100%'
    }); 
    this.container.setStyle({
      left: left + 'px',
      top:  top + 'px'
    });
  },
  
  updateContent: function(content)
  {
    if (Object.isString(content))
    {
      this.container.innerHTML = content;
    }
    else
    {
      this.container.innerHTML = "";
      this.container.appendChild(content);
    }
    
    this.container.select('.hide_dialog').each(function(cancelLink){
      cancelLink.observe('click', this.onClickHide.bind(this));
    },this);
    this.position();
  },
  
  onClickHide: function(event)
  {
    event.stop();
    this.hide();
  },

  onScroll: function(event)
  {
    this.position();
  },
  
  show: function() 
  {
    if (this.effecting) { return; }
    this.effecting = true;
    
    // Keep up with the user if he scrolls
    this.boundOnScroll = this.onScroll.bind(this);
    Event.observe(window, "scroll", this.boundOnScroll);
    
    this.position();
    new Effect.Parallel([
      new Effect.Appear(this.blackout, { from: 0, to: 0.2, sync: true }),
      new Effect.Appear(this.container, { sync: true })
    ], {
      duration: 0.25,
      afterFinish: this.doShow.bind(this)
    });
  },
  doShow: function()
  {    
    this.effecting = false;
    this.afterShown();
  },
  afterShown: function()
  {
    if (this.options.afterShown)
    {
      this.options.afterShown();
    }
  },
  
  hide: function()
  {
    if (this.effecting) { return; }
    
    this.effecting = true;
    
    if (this.boundOnScroll)
    {
      Event.stopObserving(window, "scroll", this.boundOnScroll);
      this.boundOnScroll = null;
    }
    
    new Effect.Parallel([
      new Effect.Fade(this.blackout, { sync: true }),
      new Effect.Fade(this.container, { sync: true })
    ], {
      duration: 0.25,
      afterFinish: (function() { this.effecting = false; }).bind(this)
    });
  }
});

ModalDialog.Ajax = Class.create({
  initialize: function(element, options)
  {
    if (element.match('a'))
    {
      this.href = element.href;
      this.method = 'get';
    }
    else if (element.match('input'))
    {
      var form = element.up('form');
      this.href = form.action;
      this.method = form.method;
    }
    element.observe('click', this.onClickShow.bind(this));
    
    this.options = options || {};
  },

  createDialog: function()
  {
    var loadingContainer = new Element('div')
    loadingContainer.addClassName('loading');
    
    this.dialog = new ModalDialog(loadingContainer,this.options);
  },

  onClickShow: function(event)
  {
    event.stop();
    
    if (!this.dialog)
    {
      this.createDialog();
    }
    this.dialog.show();
    
    if (!this.isLoaded)
    {
      this.load();
    }
  },
  
  load: function() 
  {
    if (!this.isLoading)
    {
      this.isLoading = true;
      new Ajax.Request(this.href, {
        method: this.method,
        onSuccess: this.doLoad.bind(this),
        onComplete: (function(xhr){this.isLoading=false;}).bind(this)
      });
    }
  },
  doLoad: function(xhr)
  {
    this.dialog.updateContent(xhr.responseText);
    this.dialog.afterShown();
    this.isLoaded = true;
  }
});

