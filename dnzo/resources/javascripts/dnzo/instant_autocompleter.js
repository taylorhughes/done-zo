/**
 *  InstantAutocompleter v0.1
 * 
 *  (c) 2009 Taylor Hughes (taylor@taylor-hughes.com)
 * 
 *  InstantAutocompleter is freely distributable under the terms 
 *  of an MIT-style license. For details, visit:
 *
 *    http://code.google.com/p/instant-autocompleter/
 *
 *  InstantAutocomplete requires Prototype 1.6.0.4
 *
 *  Usage:
 *
 *    var input = $$('input.needs-autocompleting').first();
 *
 *    var collection = ["Apple", "Orange", "Banana"];
 *      == or ==
 *    var collection = function(value) { return ['a','b','c']; }
 *  
 *    var options = {
 *      // whether or not the first match in the list is selected
 *      firstSelected: false,
 *      // limit on the number of matching results to display
 *      numResults: 5,
 *      // regex for what to look for before  match.
 *      // if you want to match any string inside, for example,
 *      // this should be empty.
 *      beforeMatch: /(?:^|\s)/,
 *      // whether or not a tab event should be successful
 *      continueTabOnSelect: true,
 *      // whether this is a tokenized, multivalue list
 *      multivalue: false,
 *      // token splitter regex if this is a multivalue list
 *      tokenSplitter: /[^\w\d_-]/,
 *      // transform separator typed when you select an item into this one instead
 *      transformSeparator: ', '
 *    };
 *
 *  new InstantAutocompleter(input, collection, options);
 *
 */
var InstantAutocompleter = Class.create({
  
  initialize: function(element, collectionOrCallback, options) 
  {
    var defaults = {
      firstSelected: false,
      continueTabOnSelect: true,
      tokenSplitter: /[,;]\s*/,
      beforeMatch: /(?:^|\s)/,
      transformSeparator: null,
      multivalue: false
    };
    this.options = Object.extend(defaults,
      (typeof options != 'undefined') ? options : {}
    );
    
    // Input element to monitor
    this.element = element;
    // Collection to snatch the choices from
    this.collectionOrCallback = collectionOrCallback;
    
    this.setupElements();
    this.wireEvents();
    this.reset();
  },
  
  setupElements: function()
  {
    this.updateElementContainer = new Element('div');
    this.updateElementContainer.hide();
    
    this.updateElement = new Element('ul');
    this.updateElement.addClassName('autocompleter');
    
    this.updateElementContainer.appendChild(this.updateElement);
    this.element.parentNode.appendChild(this.updateElementContainer);
    
    this.updateElementContainer.setStyle({
      position: 'absolute',
      zIndex: 2
    });
  },
  
  wireEvents: function() 
  {
    this.element.observe('focus',    this.onFocus.bind(this));
    this.element.observe('keydown',  this.onKeyDown.bind(this));
    this.element.observe('keypress', this.onKeyPress.bind(this));
    this.element.observe('keyup',    this.onKeyUp.bind(this));
    
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

  onKeyDown: function(event) 
  {
    this.wasShown = this.isShown();
    var stop = false;

    switch(event.keyCode) {
    case Event.KEY_TAB:
      if (this.selectEntry()) {
        this.dontReappear = true;
        stop = !this.options.continueTabOnSelect;
      }
      break;
      
    case Event.KEY_RETURN:
      if (this.selectEntry()) {
        this.dontReappear = true;
        stop = true;
      }
      break;
      
    case Event.KEY_ESC:
      this.reset();
      this.dontReappear = true;
      stop = this.wasShown;
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
      
    } // end switch keycode
    
    this.wasStopped = stop;
    if (stop)
    {
      event.stop();
    }
  },
  
  onKeyPress: function(event) 
  { 
    if (this.wasStopped) { event.stop(); }
    
    // Check if we got a real character
    var str = event.charCode > 0 && String.fromCharCode(event.charCode);
    if (!str) { return; }
  
    // Check if we got a separator; if so, we should select and allow for the next
    if (this.options.multivalue && str.match(this.options.tokenSplitter)) {
      if (this.selectEntry()) {
        event.stop();
      }
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
      // We use wasShown here because it may have
      // been visible before onKeyUp was called.
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
    var value = this.getTokens().last();
    this.value = value;
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
      li.innerHTML = match.escapeHTML();
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
    // Escape user input for regular expression
    var value = this.escapeRegex(this.value);
    var beforeMatch = this.regexToString(this.options.beforeMatch).first();
    return new RegExp(beforeMatch + value, "i");
  },
  
  getTokens: function()
  {
    var value = this.element.getValue();
    var tokens = [];
    
    if (this.options.multivalue) {
      var stringified = this.regexToString(this.options.tokenSplitter);
      var splitterMatchall = stringified.first();
      var flags = stringified.last();
      if (!flags.match(/g/)) { flags += "g"; }
      
      // to match the values
      var protokens  = value.split(this.options.tokenSplitter);
      // to match the splitters
      var antitokens = value.match(new RegExp(splitterMatchall, flags)) || [];
      
      protokens.each(function(token, index) {
        tokens.push(token);
        if (antitokens[index]) tokens.push(antitokens[index]);
      });
    }
    else
    {
      tokens.push(value);
    }
    
    return tokens;
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
    var newValue = this.getSelectedValue();
    this.reset();
    
    if (!newValue) { return false; }
    
    var tokens = this.getTokens();
    tokens = tokens.slice(0,tokens.length - 1);
    newValue = tokens.join('') + newValue;
    
    if (this.options.multivalue && this.options.transformSeparator) {
      // Use this separator instead of whatever they typed
      newValue += this.options.transformSeparator;
    }
    
    this.element.setValue(newValue);
    
    return true;
  },
  
  escapeRegex: function(str)
  {
    return str.replace(/([.*+?|(){}[\]\\])/g, '\\$1');
  },
  
  regexToString: function(regex)
  {
    var splitterMatchall = regex.toString();
    var matches = splitterMatchall.match(/^\/(.*)\/(\w*)$/);
    
    return [matches[1],matches[2]];
  }
  
});