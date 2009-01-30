/**
 *  InstantAutocompleter
 *
 *  Usage:
 *
 *    var input = $('input[type=text]');
 *
 *    var collection = ["Apple", "Orange", "Banana"];
 *      == or ==
 *    var collection = function(value) { return ['a','b','c']; }
 *  
 *    var options = {
 *      // whether or not the first match in the list is selected
 *      firstSelected: true,
 *      // limit on the number of matching results to display
 *      numResults: 5
 *    };
 *
 *  new InstantAutocompleter(input, collection, options);
 *
 *
 */
var InstantAutocompleter = Class.create({
  
  initialize: function(element, collectionOrCallback, options) 
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
    this.collectionOrCallback = collectionOrCallback;
    
    this.updateElementContainer = new Element('div');
    this.updateElementContainer.hide();
    
    this.updateElement = new Element('ul', { 
      className: 'autocompleter' 
    });
    
    this.updateElementContainer.appendChild(this.updateElement);
    this.element.parentNode.appendChild(this.updateElementContainer);
    
    this.wireEvents();
    this.reset();
  },
  
  wireEvents: function() 
  {
    this.element.observe('focus',   this.onFocus.bind(this));
    this.element.observe('keydown', this.onKeyDown.bind(this));
    this.element.observe('keyup',   this.onKeyUp.bind(this));
    
    this.updateElementContainer.observe('click',     this.onClick.bind(this));
    this.updateElementContainer.observe('mouseover', this.onHover.bind(this));
  },
  
  reset: function(event) 
  {
    this.hide();
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
  
  onHover: function(event)
  {
    var li = event.element();
    li = li.match('li') ? li : li.up('li');
    
    // Could happen on the border of the element
    if (!li) { return; }
    
    var index = li.autocompleteIndex;

    if (index != null && this.selectedIndex != index)
    {
      this.selectedIndex = index;
      this.updateSelected();
    }
  },
  
  onClick: function(event)
  {
    this.selectEntry();
    this.dontReappear = true;
    event.stop();
    this.element.focus();
  },
  
  isShown: function() 
  {
    return this.updateElementContainer.visible();
  },
  
  show: function() 
  {
    this.updateElementContainer.absolutize();
    this.updateElementContainer.setStyle({
      height: null
    });
    this.updateElementContainer.clonePosition(this.element, {
      setHeight: false,
      offsetTop: this.element.offsetHeight
    });
    this.updateElementContainer.show();
  },
  
  hide: function() 
  {
    this.updateElementContainer.hide();
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
      li.autocompleteIndex = index;
      li.innerHTML = match;
      this.updateElement.appendChild(li);
      if (match == previouslySelected) { 
        this.selectedIndex = index;
      }
    }, this);
    
    this.updateSelected();
    
    if (!this.isShown()) { 
      this.show(); 
    }
  },
  
  getCollection: function()
  {
    var collection = this.collectionOrCallback;
    if (collection instanceof Function) {
      collection = collection(this.value);
    }
    return collection;
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
    var matches = this.getCollection().collect(function(choice) {
      if (choice.match(regex)) { return choice; }
      return null;
    }).reject(function(c){ return !c; });
    
    if (matches.length == 1 && matches[0] == this.value) {
      matches = [];
    }
    
    if (this.options.numResults) {
      return matches.slice(0,this.options.numResults);
    }
    return matches;
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
    if (this.selectedIndex == this.matches.length) { return; }
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