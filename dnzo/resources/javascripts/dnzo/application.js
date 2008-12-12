var DNZO = {
  load: function(event)
  {
    // Setup dropdown switcher
    var switcher = $('switcher');
    if (switcher) switcher.observe('change', DNZO.onSwitchList); 
    
    $$('a.dialog').each(function(dialogLink) {
      new ModalDialog(dialogLink);
    });
  },
  
  onSwitchList: function(event)
  {
    document.location.href = $F(event.element());
  }  
};

Event.observe(window,'load',DNZO.load);

ModalDialog = Class.create({
  initialize: function(dialogLink) 
  {
    this.createElements();
    this.href = dialogLink.href;
    dialogLink.observe('click', this.onClickShow.bind(this));
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
    var innerContainer = new Element('div')
    innerContainer.addClassName('loading');
    this.container.appendChild(innerContainer);
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

  onClickShow: function(event)
  {
    event.stop();
    this.show();
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
    if (!this.isLoaded)
    {
      this.load();
    }
    
    this.effecting = true;
    
    // Keep up with the user if he scrolls
    this.boundOnScroll = this.onScroll.bind(this);
    Event.observe(window, "scroll", this.boundOnScroll);
    
    this.position();
    new Effect.Parallel([
      new Effect.Appear(this.blackout, { from: 0, to: 0.2, sync: true }),
      new Effect.Appear(this.container, { sync: true }),
    ], {
      duration: 0.25,
      afterFinish: (function() { this.effecting = false; }).bind(this)
    });
  },
  
  load: function() 
  {
    if (!this.isLoading)
    {
      new Ajax.Request(this.href, {
        method: 'get',
        onSuccess: this.doLoad.bind(this),
        afterComplete: (function(xhr){this.isLoading=false;}).bind(this)
      });
    }
  },
  doLoad: function(xhr)
  {
    this.container.innerHTML = xhr.responseText;
    this.container.select('.hide_dialog').each((function(cancelLink){
      cancelLink.observe('click', this.onClickHide.bind(this));
    }).bind(this));
    this.position();
    
    this.isLoaded = true;
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
      new Effect.Fade(this.container, { sync: true }),
    ], {
      duration: 0.25,
      afterFinish: (function() { this.effecting = false; }).bind(this)
    });
  }
})