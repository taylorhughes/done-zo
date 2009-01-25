var Tasks = {
  TASK_SAVED_EVENT: 'tasks:task_saved',
  TASK_EDITING_EVENT: 'tasks:task_editing',
  TASK_CANCEL_EDITING_EVENT: 'tasks:task_cancel_editing',
  
  HIDE_STATUS_DELAY: 15, // seconds
  
  load: function(event)
  {
    new ModalDialog($('add_list'), {
      afterShown: function() {
        $('new_list_name').activate();
      }
    });
    
    Tasks.table = $('tasks_list');
    
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
  
  doFail: function(xhr)
  {
    alert("Ruh roh! Something went wrong. Please let us know what happened!");
  }
};

var TaskRow = Class.create({
  
  /*** INITIALIZATION ***/
  
  initialize: function(viewRow, editRow)
  {
    this.editEventsWired = false;
    
    if (viewRow)
    {
      this.viewRow = viewRow;
      this.wireViewingEvents(this.viewRow);
      this.wireDragging(this.viewRow);
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
  },
  
  wireEditingEvents: function(row)
  {    
    var save = row.select('.edit>input[type=submit]')[0];
    save.observe('click', this.onClickSave.bind(this));
    
    row.observe('keyup', this.onKeyUp.bind(this));

    this.cancelLink = row.select('.edit>a.cancel')[0];
    this.boundOnClickCancel = this.onClickCancel.bind(this);
    this.cancelLink.observe('click', this.boundOnClickCancel);
    
    this.wireProjectAutocomplete(row);
    this.wireContextAutocomplete(row);
    
    this.editEventsWired = true;
  },
  
  wireDragging: function(row)
  {
    new Draggable(row, { 
      ghosting:   false,
      constraint: 'vertical',
      onStart:    this.onStartDrag.bind(this),
      onEnd:      this.onStopDrag.bind(this),
      onDrag:     this.onDrag.bind(this)
    });
  },
  
  wireProjectAutocomplete: function(row)
  {
    var project = row.select('td.project>input').first();

    var autocompleter = row.select('.project-autocompleter').first();
    var autocompleterLink = autocompleter.select('a').first();
  
    project.observe('keyup', function(event) {
      // Don't want <enter> while selecting an item to save the task.
      if (autocompleter.visible()) { event.stop(); }
    });
  
    new Ajax.Autocompleter(project, autocompleter, autocompleterLink.href, {
      method: 'get',
      paramName: 'q',
      frequency: 0.2
    });
  },
  
  wireContextAutocomplete: function(row)
  {
    var contexts = row.select('td.context>input').first();

    var autocompleter = row.select('.context-autocompleter').first();
    var autocompleterLink = autocompleter.select('a').first();
  
    contexts.observe('keyup', function(event) {
      // Don't want <enter> while selecting an item to save the task.
      if (autocompleter.visible()) { event.stop(); }
    });
  
    new Ajax.Autocompleter(contexts, autocompleter, autocompleterLink.href, {
      method: 'get',
      paramName: 'q',
      frequency: 0.2,
      tokens: [' ', ',', ';']
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
    this.completeOrUncomplete(check.checked, {
      onFailure: (function(xhr){
        this.doFail();
        check.checked = !checked;
      }).bind(this)
    });
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
  
  onKeyUp: function(event)
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
    
    this.findDragBounds();
  },
  
  onStopDrag: function(draggable, mouseEvent)
  {
    this.viewRow.removeClassName('dragging');
    this.viewRow.up('table').removeClassName('row-dragging');
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
    this.belowNeighbors = this.viewRow.nextSiblings().findAll(visibleRowTest);
   
    this.canMoveUp      = this.aboveNeighbors.length > 0;
    this.topDragBounds  = null;
    if (this.canMoveUp)
    {
      this.topDragBounds = this.aboveNeighbors.collect(function(aboveNeighbor) {
        return aboveNeighbor.cumulativeOffset().top + aboveNeighbor.getDimensions().height;
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
  
  completeOrUncomplete: function(complete, options)
  {
    var params = {}
    if (complete)
      params['force_complete'] = true;
    else
      params['force_uncomplete'] = true;
    
    defaultOptions = {
      method: 'post',
      parameters: params,
      onSuccess: this.doComplete.bind(this)      
    };
    if (options)
    {
      for (p in options) { defaultOptions[p] = options[p] };
    }
    
    new Ajax.Request(this.editLink.href, defaultOptions);
  },
  doComplete: function(xhr)
  {
    this.replaceRows(xhr);
  },
  
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
});

Event.observe(window,'load',Tasks.load);