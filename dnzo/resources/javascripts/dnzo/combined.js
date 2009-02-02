DNZO = Object.extend(DNZO,{
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
    if (DNZO.timezoneInfo.updateUrl.length == 0) { return; }
    
    var currentOffset = (new Date()).getTimezoneOffset();
    if (DNZO.timezoneInfo.offset != currentOffset)
    {
      new Ajax.Request(DNZO.timezoneInfo.updateUrl, {
        parameters: { offset: currentOffset },
        method: 'post'
      });
    }
  }
});

Event.observe(window,'load',DNZO.load);/**
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
 *      firstSelected: false,
 *      // limit on the number of matching results to display
 *      numResults: 5,
 *      // token splitter regex
 *      tokenSplitter: /[^\w\d_-]/,
 *      // regex for what to look for before  match.
 *      // if you want to match any string inside, for example,
 *      // this should be empty.
 *      beforeMatch: /(?:^|\s)/,
 *      // whether or not a tab event should be successful
 *      continueTabOnSelect: true,
 *      // transform separator typed when you select an item into this one instead
 *      transformSeparator: ', '
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
    
    this.updateElement = new Element('ul', { 
      className: 'autocompleter' 
    });
    
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
  
});/*
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
});var TaskRow = Class.create({
  
  /*** INITIALIZATION ***/
  
  initialize: function(viewRow, editRow)
  {
    this.editEventsWired = false;
    
    if (viewRow)
    {
      this.viewRow = viewRow;
      this.wireViewingEvents(this.viewRow);
    }
    if (editRow)
    {
      this.editRow = editRow;
      // Delay wiring up the editing events until 
      // we actually need to
      if (!viewRow || this.editRow.visible())
      {
        this.wireEditingEvents(this.editRow);
      }
    }
    
    // Need to keep this around so we can unobserve it later in destroy()
    this.boundOnOtherTaskEditing = this.onOtherTaskEditing.bind(this);
    Tasks.table.observe(Tasks.TASK_EDITING_EVENT, this.boundOnOtherTaskEditing);
  },
  
  wireViewingEvents: function(row)
  {
    this.editLink = row.select('.edit>a.edit')[0];
    this.editLink.observe('click', this.onClickEdit.bind(this));

    this.trashcan = row.select('.edit>a.delete')[0];
    this.trashcan.observe('click', this.onClickTrash.bind(this));

    var finish = row.select('.complete')[0];
    finish.observe('click', this.onClickComplete.bind(this));
    
    // For clicking events
    row.observe('dblclick', this.onDoubleClickViewRow.bind(this));
    
    this.wireDragging(this.viewRow);
  },
  
  wireEditingEvents: function(row)
  {    
    var save = row.select('.edit>input[type=submit]')[0];
    save.observe('click', this.onClickSave.bind(this));
    
    row.observe('keydown', this.onKeyDown.bind(this));

    this.cancelLink = row.select('.edit>a.cancel')[0];
    this.boundOnClickCancel = this.onClickCancel.bind(this);
    this.cancelLink.observe('click', this.boundOnClickCancel);
    
    this.wireProjectAutocomplete(row);
    this.wireContextAutocomplete(row);
    
    this.editEventsWired = true;
  },
  
  wireDragging: function(row)
  {
    if (!Tasks.sortable()) { return; }
    
    new Draggable(row, {
      starteffect: null,
      endeffect:   null,
      
      revert:      true,
      ghosting:    false,
      constraint:  'vertical',
      
      onStart:     this.onStartDrag.bind(this),
      onEnd:       this.onStopDrag.bind(this),
      onDrag:      this.onDrag.bind(this)
    });
  },
  
  wireProjectAutocomplete: function(row)
  {
    var project = row.select('td.project>input').first();

    new InstantAutocompleter(project, function(){ return DNZO.projects; }, {
      numResults: 5
    });
  },
  
  wireContextAutocomplete: function(row)
  {
    var contexts = row.select('td.context>input').first();
    
    new InstantAutocompleter(contexts, function(){ return DNZO.contexts; }, {
      numResults:    5,
      multivalue:    true,
      tokenSplitter: /[^\w\d@_-]+/,
      beforeMatch:   /(^|\s|@)/,
      transformSeparator: ' ',
      continueTabOnSelect: false
    }); 
  },
  
  destroy: function()
  {
    if (this.viewRow) this.viewRow.remove();
    if (this.editRow && this.editRow.parentNode) this.editRow.remove();
    this.ignoreCancels();
  },
  
  ignoreCancels: function()
  {
    Event.stopObserving(this.cancelLink, 'click', this.boundOnClickCancel);
    this.cancelLink.href = null;
    Event.stopObserving(Tasks.table, Tasks.TASK_EDITING_EVENT, this.boundOnOtherTaskEditing);
  },
  
  /*** MISC ***/
  
  isEditing: function()
  {
    return this.editRow && this.editRow.visible();
  },
  
  isCompleted: function()
  {
    return this.viewRow && this.viewRow.hasClassName('completed');
  },
  
  fire: function(eventName, memo)
  {
    Event.fire((this.viewRow || this.editRow), eventName, memo);
  },
  
  taskAbove: function()
  {
    var above = this.viewRow.previousSiblings().find(function(row) { 
      return row.match('tr.task-row') && ! row.hasClassName('editable');
    });
    return Tasks.idFromViewRow(above);
  },
  
  taskBelow: function()
  {
    var below = this.viewRow.nextSiblings().find(function(row) { 
      return row.match('tr.task-row') && ! row.hasClassName('editable');
    });
    return Tasks.idFromViewRow(below);
  },
  
  /*** EVENT HANDLERS ***/
  
  onClickEdit: function(event)
  {
    event.stop();
    this.edit();
    this.activate();
  },
  
  onClickCancel: function(event)
  {
    event.stop();
    this.cancel();
  },
  
  onClickTrash: function(event)
  {
    event.stop();
    this.trash();
  },
  
  onClickSave: function(event)
  {
    var pointer = {
      x: event.pointerX(),
      y: event.pointerY()
    }
    
    if (pointer.x != 0 || pointer.y != 0)
    {
      var element = event.element();
      var dimensions = element.getDimensions();
      var position = element.cumulativeOffset();
      
      // We have to verify the click actually clicked this button because IE
      // assigns pointer.x and pointer.y to nonzero values even if it was 
      // not triggered by an actual click on that button, unlike Firefox and
      // Safari which assign x and y to be zero in that case.
      inX = pointer.x >= position.left && pointer.x <= position.left + dimensions.width;
      inY = pointer.y >= position.top  && pointer.y <= position.top + dimensions.height;
      
      if (inX && inY)
      {
        this.save();
      }
    }

    event.stop();
  },
  
  onClickComplete: function(event)
  {
    if (this.isEditing()) return;
    
    var check = event.element();
    var checked = check.checked;
    this.completeOrUncomplete(checked);
  },
  
  onDoubleClickViewRow: function(event)
  {
    event.stop();
    
    var element = event.element();
    var td = (element.match('td')) ? element : element.up('td');
    var className = null;
    
    if (td)
    {
      className = td.classNames().toArray().first();
      // Double-clicking the edit/delete link or the checkbox should not edit
      if (['edit','done'].include(className))
      {
        return;
      }
    } 
    
    this.edit();
    this.activate(className);
  },
  
  onKeyDown: function(event)
  {
    switch(event.keyCode)
    {
      case Event.KEY_RETURN:
        this.save();
        break;
        
      case Event.KEY_ESC:
        this.cancel();
        break;
    }    
  },

  onOtherTaskEditing: function(event)
  {
    if (this.isEditing())
    {
      this.cancel();
    }
  },
  
  /** DRAG AND DROP **/
  
  onStartDrag: function(draggable, mouseEvent)
  {
    this.viewRow.addClassName('dragging');
    this.viewRow.up('table').addClassName('row-dragging');
    
    this.recordPosition();
    this.findDragBounds();
  },
  
  onStopDrag: function(draggable, mouseEvent)
  {
    this.viewRow.removeClassName('dragging');
    this.viewRow.up('table').removeClassName('row-dragging');
    
    this.savePosition();
  },
  
  onDrag: function(draggable, mouseEvent)
  {
    var scrollOffset = document.viewport.getScrollOffsets().top;
    var y = mouseEvent.clientY + scrollOffset;
    
    var visibleRow, rowBound = null;
    var index = 0;
    if (this.canMoveUp && y < this.topDragBounds.first())
    {
      if (this.topDragBounds.length > 1)
      {
        rowBound = this.topDragBounds.find(function(bound) { return y > bound; });
        index = rowBound ? this.topDragBounds.indexOf(rowBound) - 1 : this.topDragBounds.length - 1;
      }
      visibleRow = this.aboveNeighbors[index];
      this.moveUp(visibleRow);
    }
    else if (this.canMoveDown && y > this.bottomDragBounds.first())
    {
      if (this.bottomDragBounds.length > 1)
      {
        rowBound = this.bottomDragBounds.find(function(bound) { return y < bound; });
        index = rowBound ? this.bottomDragBounds.indexOf(rowBound) - 1 : this.bottomDragBounds.length - 1;
      }
      visibleRow = this.belowNeighbors[index];
      this.moveDown(visibleRow);
    }
  },
  
  findDragBounds: function()
  {    
    var visibleRowTest = function(e){ return e.match('tr.task-row') && e.visible(); }
    this.aboveNeighbors = this.viewRow.previousSiblings().findAll(visibleRowTest);
    this.belowNeighbors = this.viewRow.nextSiblings().findAll(visibleRowTest).reject(
      function(e) { return e.hasClassName('unsaved'); }
    );
   
    var myHeight = this.viewRow.getDimensions().height;
   
    this.canMoveUp      = this.aboveNeighbors.length > 0;
    this.topDragBounds  = null;
    if (this.canMoveUp)
    {
      this.topDragBounds = this.aboveNeighbors.collect(function(aboveNeighbor) {
        var hisHeight = aboveNeighbor.getDimensions().height;
        return aboveNeighbor.cumulativeOffset().top + hisHeight -
               // If this row is taller than my row, when my row moves
               // I don't want the mouse to end up in his row -- so add
               // the difference in height as a buffer.
               (hisHeight > myHeight ? hisHeight - myHeight : 0);
      });
    }
    
    this.canMoveDown      = this.belowNeighbors.length > 0;
    this.bottomDragBounds = null;
    if (this.canMoveDown)
    {
      this.bottomDragBounds = this.belowNeighbors.collect(function(belowNeighbor) {
        return belowNeighbor.cumulativeOffset().top;
      });
    }
  },
  
  moveUp: function(visibleRow)
  {
    // If the above neighbor is an edit row, just use it because it's the top row
    // otherwise we have to get the row above it
    var aboveEditRow = visibleRow.hasClassName('editable') ? 
                       visibleRow : visibleRow.previousSiblings()[0];
    
    this.moveAboveRow(aboveEditRow);
    this.findDragBounds();
  },
  
  moveDown: function(visibleRow)
  {
    // This is the row BELOW the below neighbor, since we're going to take
    // our rows and insert them ** BEFORE ** this element 
    var nextBelowNeighbor = visibleRow.hasClassName('editable') ? 
                            visibleRow.nextSiblings()[1] : 
                            visibleRow.nextSiblings()[0];
    
    this.moveAboveRow(nextBelowNeighbor);
    this.findDragBounds();
  },
  
  moveAboveRow: function(rowBelow)
  {
    this.viewRow.remove();
    this.editRow.remove();
    
    rowBelow.parentNode.insertBefore(this.editRow, rowBelow);
    rowBelow.parentNode.insertBefore(this.viewRow, rowBelow);
  },
  
  /*** ACTIONS ***/

  edit: function()
  {
    // Can't edit completed tasks.
    if (this.isCompleted()) { return; }
    
    this.fire(Tasks.TASK_EDITING_EVENT);
    
    if (!this.editEventsWired)
    {
      this.wireEditingEvents(this.editRow);
    }
    
    this.viewRow.hide();
    this.editRow.show();
    this.activate();
  },
  
  cancel: function()
  {
    this.fire(Tasks.TASK_CANCEL_EDITING_EVENT);
    
    if (this.viewRow)
    {
      this.viewRow.show();
      this.editRow.hide();
    }
    else
    {
      // New task; can't toggle
      this.destroy();
    }
  },
  
  trash: function()
  {
    if (! this.requestedTrash)
    {
      this.requestedTrash = true;
      new Ajax.Request(this.trashcan.href, {
        method: 'get',
        onSuccess: this.doTrash.bind(this),
        onFailure: this.doFail.bind(this),
        onComplete: (function(xhr){this.requestedTrash=false;}).bind(this)
      });
    }
  },
  doTrash: function(xhr)
  {
    Tasks.updateStatusFromResponse(xhr);
    this.destroy();
  },
  
  save: function()
  {
    if (! this.isSaving)
    {
      this.isSaving = true;
      
      var action = null;
      if (this.viewRow)
      {
        action = this.editLink.href;
      }
      
      Tasks.saveTask(action, this.editRow,{
        onSuccess: this.doSave.bind(this),
        onFailure: this.doFail.bind(this),
        onComplete: (function(xhr){this.isSaving=false;}).bind(this)
      });
    
      this.editRow.select('input').each(function(e) {
        e.disable();
      })
    
      this.ignoreCancels();
      this.fire(Tasks.TASK_SAVED_EVENT, this.editRow); 
    }
  },
  doSave: function(xhr)
  { 
    this.replaceRows(xhr);
  },
  
  completeOrUncomplete: function(complete)
  {
    var params = {}
    var editingCheck = this.editRow && this.editRow.select('input.complete').first();
    if (editingCheck) { editingCheck.checked = complete; }
    
    if (complete)
    {
      params['force_complete'] = true;
      this.viewRow.addClassName('completed');
    }
    else
    {
      params['force_uncomplete'] = true;
      this.viewRow.removeClassName('completed');
    }
    
    new Ajax.Request(this.editLink.href, {
      method: 'post',
      parameters: params,
      onSuccess: this.doComplete.bind(this),
      onFailure: this.doFail.bind(this)
    });
  },
  doComplete: function(xhr) {},
  
  recordPosition: function()
  {
    var originalPosition = this.position;
    this.position = {
      task_above: this.taskAbove(),
      task_below: this.taskBelow()
    }
    
    // Returns whether we changed anything
    return Object.toJSON(originalPosition||{}) != Object.toJSON(this.position);
  },
  
  savePosition: function()
  {
    if (!Tasks.sortable()) { return; }
    
    if (this.recordPosition())
    {
      new Ajax.Request(this.editLink.href, {
        method: 'post',
        onSuccess: this.doSavePosition.bind(this),
        onFailure: this.doFail.bind(this),
        parameters: this.position
      });
    }
  },
  doSavePosition: function(xhr) {},
  
  doFail: function(xhr)
  {
    // TODO: Do something useful when this fails.
    Tasks.doFail(xhr);
  },
  
  replaceRows: function(xhr)
  {
    // May be adding a new task
    if (this.viewRow)
    {
      this.viewRow.remove();
    }
   
    var tbody = this.editRow.parentNode; 
    var temp = Tasks.containerFromResponse(xhr);
    var rows = temp.select('tr');

    var newEditRow = rows.find(function(row){ return row.hasClassName('editable'); });
    var newViewRow = rows.without(newEditRow)[0];
    
    tbody.insertBefore(newEditRow, this.editRow);
    tbody.insertBefore(newViewRow, this.editRow);
    
    this.editRow.remove();
    // Re-initialize everything.
    this.initialize(newViewRow, newEditRow);
  },
  
  activate: function(tdClassName)
  {
    if (!this.editRow) return;
    
    if (!tdClassName)
    {
      var body = this.editRow.select('td.task>input').first();
      var project = this.editRow.select('td.project>input').first();
    
      if (body && project)
      {
        var projectIsVisible = project.getDimensions().width > 0;
        if (body.getValue().blank() && project.getValue().blank() && projectIsVisible)
        { 
          project.activate();
        }
        else
        {
          body.activate();
        }
      }
    }
    else
    {
      var input = this.editRow.select('td.' + tdClassName + '>input').first();
      if (input) { input.activate(); }
    }
  }
});var Tasks = {
  TASK_SAVED_EVENT: 'tasks:task_saved',
  TASK_EDITING_EVENT: 'tasks:task_editing',
  TASK_CANCEL_EDITING_EVENT: 'tasks:task_cancel_editing',
  
  HIDE_STATUS_DELAY: 15, // seconds
  
  load: function(event)
  {
    Tasks.table = $('tasks_list');
    
    if (!Tasks.table || Tasks.table.hasClassName('archived')) { return; }
    
    new ModalDialog($('add_list'), {
      afterShown: function() {
        $('new_list_name').activate();
      }
    });
    
    Tasks.addRow = Tasks.table.select('#add_row')[0];
    Tasks.addLink = Tasks.addRow.select('#add')[0];
    
    Tasks.tasksForm = $('tasks_form');
    Tasks.newTaskTableHTML = Tasks.tasksForm.innerHTML;
  
    Tasks.addLink.observe('click', Tasks.onClickAddTask);
  
    var rows = Tasks.table.select('tr.task-row');
    for (var i = 0; i < rows.length; i += 2)
    {
      // NOTE: This makes us depdendent on the order that these
      //       rows are output. That is not good, but this is fast.
      new TaskRow(rows[i + 1], rows[i]);
    }
    
    Tasks.setHideStatus();
  },
  
  sortable: function() {
    return Tasks.table.hasClassName('sortable');
  },
  
  onClickAddTask: function(event)
  {
    event.stop();
    
    Tasks.cancelAll();
    
    Tasks.doAddNewTask(Tasks.getNewTaskRow(), event.memo);
  },
  
  addCanceled: function(event)
  {
    Tasks.addRow.show();
    Event.stopObserving(Tasks.table, Tasks.TASK_SAVED_EVENT, Tasks.addSaved);
    event.stop();
  },
  
  addSaved: function(event)
  {
    Tasks.onClickAddTask(event); 
  },
  
  doAddNewTask: function(row, existingTask)
  {
    var tbody = Tasks.table.select('tbody')[0];

    Tasks.addRow.remove();
    tbody.insert(row);
    tbody.insert(Tasks.addRow);
    
    if (existingTask)
    {
      ['context','project'].each(function(className){
        var selector = 'td.' + className + '>input';
        var oldinput = existingTask.select(selector).first();
        var newinput = row.select(selector).first();
        
        if (newinput && oldinput)
        {
          newinput.setValue(oldinput.getValue());
        }
      });
    }

    var task = new TaskRow(null, row);
    Tasks.table.observe(Tasks.TASK_SAVED_EVENT, Tasks.addSaved);
    row.observe(Tasks.TASK_CANCEL_EDITING_EVENT, Tasks.addCanceled);
    
    Tasks.addRow.hide();
    task.activate();
  },
  
  cancelAll: function()
  {
    Event.fire(Tasks.table, Tasks.TASK_EDITING_EVENT);
  },
  
  loadStatus: function(container)
  {
    //
    // container.select("#status") is broken because disconnected
    // nodes with the same ID as a connected nodes are not OK in this
    // version of prototype. Stupid.
    //
    var status = container.select("div").find(function(div){
      return div.id == "status";
    });
    
    if (!status)
    {
      return;
    }
    
    var existingStatus = $("status");
    if (existingStatus)
    {
      existingStatus.innerHTML = status.innerHTML;
      status = existingStatus;
    }
    else
    {
      status.hide();
      Tasks.table.up('div').appendChild(status);
    }
    
    Tasks.showStatus();
    Tasks.setHideStatus();
  },
  
  setHideStatus: function()
  {
    if (Tasks.hideStatusTimeout)
    {
      clearTimeout(Tasks.hideStatusTimeout);
    }
    Tasks.hideStatusTimeout = setTimeout(Tasks.hideStatus, Tasks.HIDE_STATUS_DELAY * 1000);
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
  
  showStatus: function()
  {
    var status = $('status');
    if (!status || status.visible()) { return; }
    
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
  
  updateStatusFromResponse: function(xhr)
  {
    Tasks.loadStatus(Tasks.containerFromResponse(xhr));
  },
  
  updateProjects: function(row)
  {
    var project = row.select('td.project>input').first();
    project = project && project.getValue();
    if (!project) { return; }
    
    DNZO.projects = [project, DNZO.projects.without(project)].flatten();
  },
  
  updateContexts: function(row)
  {
    var contexts = row.select('td.context>input').first();
    contexts = contexts && contexts.getValue();
    if (!contexts) { return; }
    
    contexts.split(/[,;\s]+/).each(function(context){
      // copy django's slugify method
      context = context.replace(/[^\w\s-]/, '').strip().toLowerCase();
      context = "@" + context.replace(/[-\s]+/, '-');
      
      DNZO.contexts = [context, DNZO.contexts.without(context)].flatten();
    });
  },
  
  saveTask: function(action, row, options)
  {
    var duplicateBySelector = function(from,to,selector) {
      var fromFields = from.select(selector);
      var toFields   = to.select(selector);
      
      if (fromFields.length != toFields.length) return;
      
      var i = 0;
      fromFields.each(function(fromField) {
        toFields[i].setValue(fromField.getValue());
        i += 1;
      });
    }
    
    duplicateBySelector(row, Tasks.tasksForm, 'input[type=text]');
    var chk = 'input[type=checkbox]';
    
    Tasks.tasksForm.select(chk)[0].checked = row.select(chk)[0].checked;
     
    var oldAction = Tasks.tasksForm.action;

    Tasks.tasksForm.action = action ? action : oldAction;
    Tasks.tasksForm.request(options);
    Tasks.tasksForm.action = oldAction;
    
    Tasks.updateProjects(row);
    Tasks.updateContexts(row);
  },
  
  getNewTaskRow: function()
  {
    var temp = new Element('div');
    temp.innerHTML = Tasks.newTaskTableHTML;
    return temp.select("tr")[0];
  },
  
  containerFromResponse: function(xhr)
  {
    var temp = new Element('div');
    temp.innerHTML = xhr.responseText;
    return temp;
  },
  
  idFromViewRow: function(row)
  {
    var input = row && row.select('input.task-id').first();
    if (input)
      return input.getValue();
    return null;
  },
  
  doFail: function(xhr)
  {
    alert("Ruh roh! Something went wrong. Please let us know what happened!");
  }
};

Event.observe(window,'load',Tasks.load);