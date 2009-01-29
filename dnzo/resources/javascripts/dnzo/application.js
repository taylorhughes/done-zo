var DNZO = {
  load: function(event)
  {
    // Setup dropdown switcher
    var switcher = $('switcher');
    if (switcher) switcher.observe('change', DNZO.onSwitchList); 
    
    $$('a.dialog').each(function(dialogLink) {
      new ModalDialog(dialogLink);
    });
    
    DNZO.verifyTimezone();
  },
  
  onSwitchList: function(event)
  {
    document.location.href = $F(event.element());
  },
  
  verifyTimezone: function()
  {
    if (typeof TimezoneInfo == 'undefined' || TimezoneInfo.updateUrl.length == 0) { return; }
    
    var currentOffset = (new Date()).getTimezoneOffset();
    if (TimezoneInfo.offset != currentOffset)
    {
      new Ajax.Request(TimezoneInfo.updateUrl, {
        parameters: { offset: currentOffset },
        method: 'post'
      });
    }
  }
};

Event.observe(window,'load',DNZO.load);


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
ModalDialog = Class.create({
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
    
    this.createElements();
    
    this.options = options || {};
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
    if (!this.isLoaded) { return; }
    
    if (this.options.afterShown)
    {
      this.options.afterShown();
    }
  },
  
  load: function() 
  {
    if (!this.isLoading)
    {
      new Ajax.Request(this.href, {
        method: this.method,
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
    
    this.afterShown();
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


ArrayAutocompleter = Class.create({
  
  initialize: function(element, updateElement, collection) {
    // Input element to monitor
    this.element = element;
    // Element that contains the selection list
    this.updateElement = updateElement;
    // Collection to snatch the choices from
    this.collection = collection;
    
    this.wireEvents();
  },
  
  wireEvents: function() {
    this.element.observe('focus', this.onFocus.bind(this));
    this.element.observe('keydown', this.onKeyDown.bind(this));
    this.element.observe('keyup', this.onKeyUp.bind(this));
  },
  
  reset: function(event) {
    this.hide();
    this.updateElement.innerHTML = '';
    this.dontReappear = false;
    this.selectedIndex = 0;
    this.value = null;
    this.matches = [];
  },
  
  onFocus: function(event) {
    this.reset();
  },
  
  onKeyDown: function(event) {
    this.wasShown = this.isShown();
    
    if (this.dontReappear) { return; }

    switch(event.keyCode) {
      case Event.KEY_TAB:
      case Event.KEY_RETURN:
        this.selectEntry();
        return;
        
      case Event.KEY_ESC:
        this.hide();
        this.dontReappear = true;
        event.stop();
        return;
        
      case Event.KEY_LEFT:
      case Event.KEY_RIGHT:
        return;
        
      case Event.KEY_UP:
        this.markPrevious();
        event.stop();
        return;
        
      case Event.KEY_DOWN:
        this.markNext();
        event.stop();
        return;
    }
  },
  
  onKeyUp: function(event) {
    var changed = this.valueChanged();
    
    if (this.value.blank())
    {
      this.reset();
    }
    else 
    {
      if (this.wasShown) { event.stop(); }
      if (changed && !this.dontReappear) { 
        this.updateOptions(); 
      }
    }
  },
  
  isShown: function() {
    return this.updateElement.visible();
  },
  
  show: function() {
    this.updateElement.absolutize();
    this.updateElement.setStyle({
      height: null
    });
    Position.clone(this.element, this.updateElement, {
      setHeight: false,
      offsetTop: this.element.offsetHeight
    });
    this.updateElement.show();
  },
  
  hide: function() {
    this.updateElement.hide();
  },
  
  valueChanged: function() {
    var oldValue = this.value;
    this.value = this.element.getValue();
    return this.value != oldValue;
  },
  
  updateOptions: function() {
    this.updateElement.innerHTML = '';
    
    this.matches = this.getMatches();
    if (this.matches.length > 0) {
      var ul = new Element('ul');
      this.matches.each(function(match){
        var li = new Element('li');
        li.innerHTML = match;
        ul.appendChild(li);
      });
      this.updateElement.appendChild(ul);
      
      this.selectedIndex = this.selectedIndex >= this.matches.length ? this.matches.length : this.selectedIndex;
      
      this.updateSelected();
      
      if (!this.isShown()) { this.show(); }
    } else {
      this.hide();
    }
  },
  
  updateSelected: function() {
    var elements = this.updateElement.select('ul>li');
    elements.each(function(li,index){
      li.removeClassName('selected');
    });
    if (elements[this.selectedIndex]) { 
      elements[this.selectedIndex].addClassName('selected'); 
    }
  },
  
  getMatches: function() {
    var regex = this.getRegex();
    return this.collection.collect(function(choice) {
      if (choice.match(regex)) { return choice; }
      return null;
    }).reject(function(c){ return !c; });
  },
  
  getRegex: function() {
    return new RegExp('\\b' + this.value, "i");
  },
  
  markPrevious: function() {
    if (this.selectedIndex == 0) { return; }
    this.selectedIndex -= 1;
    this.updateSelected();
  },
  
  markNext: function() {
    if (this.selectedIndex == this.matches.length - 1) { return; }
    this.selectedIndex += 1;
    this.updateSelected();
  },
  
  selectEntry: function() {
    if (this.matches[this.selectedIndex]) {
      this.element.setValue(this.matches[this.selectedIndex]);
    }
    this.reset();
  }
  
});

