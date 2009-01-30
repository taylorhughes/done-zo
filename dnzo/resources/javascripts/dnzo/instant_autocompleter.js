/**
 * InstantAutocompleter
 *
 *  Usage:
 *
 *    var collection = ["Apple", "Orange", "Banana"];
 *    new InstantAutocompleter($('input[type=text]'), collection, options);
 *
 */
var InstantAutocompleter = Class.create({
  
  initialize: function(element, collection, options) 
  {
    var defaults = {
      firstSelected: true
    };
    this.options = Object.extend(defaults,
      (typeof options != 'undefined') ? options : {}
    );
    
    // Input element to monitor
    this.element = element;
    // Collection to snatch the choices from
    this.collection = collection;
    
    this.updateElement = new Element('ul', { 
      className: 'autocompleter' 
    });
    this.updateElement.hide();
    this.element.parentNode.appendChild(this.updateElement);
    
    this.wireEvents();
    this.reset();
  },
  
  wireEvents: function() 
  {
    this.element.observe('focus',   this.onFocus.bind(this));
    this.element.observe('keydown', this.onKeyDown.bind(this));
    this.element.observe('keyup',   this.onKeyUp.bind(this));
  },
  
  reset: function(event) 
  {
    this.updateElement.hide();
    this.selectedIndex = -1;
    this.value         = null;
    this.dontReappear  = false;
    this.matches       = [];
  },
  
  onFocus: function(event) 
  {
    this.reset();
  },
  
  //
  //  In keydown, I can stop events before they happen.
  //  if an Event.KEY_TAB is stopped, the user's tab action will not continue
  //  up the event chain, so they won't, for example, go to the next cell.
  //
  onKeyDown: function(event) 
  {
    this.wasShown = this.isShown();
    
    if (this.dontReappear) { return; }

    var stop = false;

    switch(event.keyCode) {
      case Event.KEY_TAB:
      case Event.KEY_RETURN:
        this.selectEntry();
        this.dontReappear = true;
        break;
        
      case Event.KEY_ESC:
        this.hide();
        this.dontReappear = true;
        stop = true;
        break;
        
      case Event.KEY_LEFT:
      case Event.KEY_RIGHT:
        break;
        
      case Event.KEY_UP:
        this.markPrevious();
        stop = true;
        break;
        
      case Event.KEY_DOWN:
        this.markNext();
        stop = true;
        break;
    }
    
    if (stop)
    {
      event.stop();
    }
  },
  
  onKeyUp: function(event) 
  {
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
  
  isShown: function() 
  {
    return this.updateElement.visible();
  },
  
  show: function() 
  {
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
  
  hide: function() 
  {
    this.updateElement.hide();
  },
  
  valueChanged: function()
  {
    var oldValue = this.value;
    this.value = this.element.getValue();
    return this.value != oldValue;
  },
  
  updateOptions: function() 
  {
    var previouslySelected = this.getSelectedValue();
    this.updateElement.innerHTML = '';
    this.matches = this.getMatches();
    
    if (this.matches.length == 0)
    {
      this.hide();
      return;
    }
    
    this.selectedIndex = this.options.firstSelected ? 0 : -1;
    this.matches.each(function(match, index){
      var li = new Element('li');
      li.innerHTML = match;
      this.updateElement.appendChild(li);
      if (match == previouslySelected) { this.selectedIndex = index; }
    }, this);
    
    this.updateSelected();
    
    if (!this.isShown()) { 
      this.show(); 
    }
  },
  
  getSelectedValue: function()
  {
    return this.matches[this.selectedIndex];
  },
  
  getSelectedElement: function()
  {
    return this.updateElement.select('li')[this.selectedIndex];
  },
  
  updateSelected: function() 
  {
    var elements = this.updateElement.select('li');
    elements.each(function(li,index){
      li.removeClassName('selected');
    });
    var selected = this.getSelectedElement();
    if (selected) { 
      selected.addClassName('selected'); 
    }
  },
  
  getMatches: function() 
  {
    var regex = this.getRegex();
    return this.collection.collect(function(choice) {
      if (choice.match(regex)) { return choice; }
      return null;
    }).reject(function(c){ return !c; });
  },
  
  getRegex: function() 
  {
    return new RegExp('\\b' + this.value, "i");
  },
  
  markPrevious: function() 
  {
    if (this.selectedIndex < 0) { return; }
    this.selectedIndex -= 1;
    this.updateSelected();
  },
  
  markNext: function() 
  {
    if (this.selectedIndex == this.matches.length - 1) { return; }
    this.selectedIndex += 1;
    this.updateSelected();
  },
  
  selectEntry: function() 
  {
    var selected = this.getSelectedValue();
    if (selected) {
      this.element.setValue(selected);
    }
    this.reset();
  }
  
});