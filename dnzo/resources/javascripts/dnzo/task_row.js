var TaskRow = Class.create({
  
  /*** INITIALIZATION ***/
  
  initialize: function(viewRow, editRow)
  {
    this.editEventsWired = false;
    
    if (editRow)
    {
      this.editRow = editRow;
      // Delay wiring up the editing events until 
      // we actually need to
      if (!viewRow || this.editRow.visible())
      {
        this.wireEditingEvents();
      }
    }
    if (viewRow)
    {
      this.viewRow = viewRow;
      this.wireViewingEvents();
      this.wireDragging();
      this.wireSorting();
    }
    
    // Need to keep this around so we can unobserve it later in destroy()
    this.boundOnOtherTaskEditing = this.onOtherTaskEditing.bind(this);
    Tasks.table.observe(Tasks.TASK_EDITING_EVENT, this.boundOnOtherTaskEditing);
    
    this.boundOnIdentifyByRow = this.onIdentifyByRow.bind(this);
    Tasks.table.observe(Tasks.TASK_IDENTIFY_BY_ROW_EVENT, this.boundOnIdentifyByRow);
  },
  
  wireViewingEvents: function()
  {
    this.editLink = this.viewRow.select('.edit>a.edit')[0];
    this.editLink.observe('click', this.onClickEdit.bind(this));

    this.trashcan = this.viewRow.select('.cancel>a.delete')[0];
    this.trashcan.observe('click', this.onClickTrash.bind(this));

    var finish = this.viewRow.select('.complete')[0];
    finish.observe('click', this.onClickComplete.bind(this));
    
    // For clicking events
    this.viewRow.observe('dblclick', this.onDoubleClickViewRow.bind(this));
    
    Tasks.table.observe(Tasks.TASKS_DRAGGABLE_EVENT, this.onTasksDraggable.bind(this));
    Tasks.table.observe(Tasks.TASKS_NOT_DRAGGABLE_EVENT, this.onTasksNotDraggable.bind(this));
  },
  
  wireEditingEvents: function()
  {    
    this.saveButton = this.editRow.select('.edit>input[type=submit]')[0];
    this.saveButton.observe('click', this.onClickSave.bind(this));
    
    this.editRow.observe('keydown', this.onKeyDown.bind(this));
    this.editRow.observe('dblclick', this.onDoubleClickEditRow.bind(this));

    this.cancelLink = this.editRow.select('.cancel>a.cancel')[0];
    this.boundOnClickCancel = this.onClickCancel.bind(this);
    this.cancelLink.observe('click', this.boundOnClickCancel);
    
    this.wireProjectAutocomplete();
    this.wireContextAutocomplete();
    
    this.editEventsWired = true;
  },
  
  wireDragging: function()
  {
    this.dragger = new Draggable(this.viewRow, {
      handle: this.viewRow.select('td.done').first(),
      
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
  
  wireSorting: function()
  {
    this.boundOnSortRequest = this.onSortRequest.bind(this);
    Tasks.table.observe(Tasks.TASK_REQUEST_SORT_EVENT, this.boundOnSortRequest);

    var due = $F(this.editRow.select('td.due>input').first()).split("/");
    if (due.length == 3)
    {
      due = due[2] + 
        ((due[0].length == 1) ? "0" : "") + due[0] + 
        ((due[1].length == 1) ? "0" : "") + due[1];
    } else {
      due = "";
    }
    
    this.sorting = {
      done:      this.isCompleted() ? 't' : 'f',
      project:   $F(this.editRow.select('td.project>input').first()),
      task:      $F(this.editRow.select('td.task>input').first()),
      context:   $F(this.editRow.select('td.context>input').first()),
      due:       due,
      createdAt: parseInt($F(this.editRow.select('input.created_at').first()))
    };      
  },
  
  wireProjectAutocomplete: function(row)
  {
    var project = this.editRow.select('td.project>input').first();

    new InstantAutocompleter(project, function(){ return DNZO.projects; }, {
      numResults: 5
    });
  },
  
  wireContextAutocomplete: function(row)
  {
    var contexts = this.editRow.select('td.context>input').first();
    
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
    Event.stopObserving(Tasks.table, Tasks.TASK_EDITING_EVENT, this.boundOnOtherTaskEditing);
    if (this.boundOnSortRequest)
    {
      Event.stopObserving(Tasks.table, Tasks.TASK_REQUEST_SORT_EVENT, this.boundOnSortRequest);
    }
    Event.stopObserving(Tasks.table, Tasks.TASK_IDENTIFY_BY_ROW_EVENT, this.boundOnIdentifyByRow);
    Event.stopObserving(this.cancelLink, 'click', this.boundOnClickCancel);
    this.cancelLink.hide();
    
    this.editRow.select('input').each(function(e) {
      e.disable();
      // Add a class name so we can style these; Safari does some weird things with disabled fields
      e.addClassName('disabled');
    });
  },
  
  unignoreCancels: function()
  {
    Tasks.table.observe(Tasks.TASK_EDITING_EVENT, this.boundOnOtherTaskEditing);
    if (this.boundOnSortRequest) 
    {
      Tasks.table.observe(Tasks.TASK_REQUEST_SORT_EVENT, this.boundOnSortRequest);
    }
    Tasks.table.observe(Tasks.TASK_IDENTIFY_BY_ROW_EVENT, this.boundOnIdentifyByRow);
    this.cancelLink.observe('click', this.boundOnClickCancel);
    this.cancelLink.show();
    
    this.editRow.select('input').each(function(e) {
      e.enable();
    });
  },
  
  /*** SORTING ***/
  
  onSortRequest: function(event)
  {
    (event.memo || []).push(this);
  },
  
  removeRows: function()
  {
    if (this.editRow) this.editRow.remove();
    if (this.viewRow) this.viewRow.remove();
  },
  
  addRowsBefore: function(element)
  {
    if (this.editRow) Insertion.Before(element, this.editRow);
    if (this.viewRow) Insertion.Before(element, this.viewRow);
  },
  
  compareTo: function(otherTask, column, descending)
  { 
    var a = this.sorting[column] || "";
    var b = otherTask.sorting[column] || "";

    if (typeof descending == "undefined") { descending = false; }
    
    // Note: strcmp in this case is not reversed for descending
    // because we are not reversing the secondary sort order
    // (we are emulating ORDER BY column DESC created_at ASC)
    if (!column || DNZO.strcmp(a,b) == 0)
    { 
      return this.sorting.createdAt - otherTask.sorting.createdAt;
      // to sort secondarily by task body
      //return DNZO.strcmp(this.task(),otherTask.task());
    }

    var cmp = DNZO.strcmp(a,b);
    if (descending) { cmp *= -1; }
    return cmp;
  },
  
  /*** MISC ***/
  
  taskID: function()
  {
    var input = this.viewRow && this.viewRow.select('input.task-id').first();
    if (input) return input.getValue();
    return null;
  },
  
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
  
  findTaskAbove: function()
  {
    var above = this.viewRow.previousSiblings().find(function(row) { 
      return row.match('tr.task-row') && ! row.hasClassName('editable');
    });
    return Tasks.taskFromRow(above);
  },
  
  findTaskBelow: function()
  {
    var below = this.viewRow.nextSiblings().find(function(row) { 
      return row.match('tr.task-row') && ! row.hasClassName('editable');
    });
    return Tasks.taskFromRow(below);
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
  
  onDoubleClickEditRow: function(event)
  {
    event.stop();
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
      if (['done','edit','cancel'].include(className))
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
        event.stop();
        break;
        
      case 32: // space
        if (this.saveButton == event.element())
        {
          this.save();
        }
        break;
        
      case Event.KEY_ESC:
        this.cancel();
        event.stop();
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
  
  onIdentifyByRow: function(event)
  {
    var row = event.memo && event.memo.row;

    if (row && (this.viewRow == row || this.editRow == row))
    {
      event.memo.task = this;
    }
    
    event.stop();
  },
  
  /** DRAG AND DROP **/
  
  onTasksDraggable: function(event)
  {
    this.wireDragging(this.viewRow);
  },
  
  onTasksNotDraggable: function(event)
  {
    if (this.dragger) 
    {
      this.dragger.destroy();
      this.dragger = null;
    }
  },
  
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
      this.viewRow.hide();
      new Ajax.Request(this.trashcan.href, {
        method: 'get',
        onComplete: this.bindOnComplete({
          onSuccess: this.doTrash,
          onFailure: function(xhr) {
            this.viewRow.show();
          },
          onComplete: function(xhr) {
            this.requestedTrash = false;
          }
        })
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
        onComplete: this.bindOnComplete({
          onSuccess: this.doSave,
          onFailure: function(xhr){
            this.unignoreCancels();
            this.cancel();
          },
          onComplete: function(xhr){
            this.isSaving=false;
          }
        })
      });
    
      this.ignoreCancels();
      this.fire(Tasks.TASK_SAVED_EVENT, this.editRow); 
    }
  },
  doSave: function(xhr)
  { 
    var replaced = this.replaceRows(xhr);
    
    // This should not happen unless the task was not saved.
    if (!replaced)
    {
      Tasks.showError('TASKS_LIMIT_ERROR');
      this.destroy();
    }
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
      this.sorting.done = 't';
    }
    else
    {
      params['force_uncomplete'] = true;
      this.viewRow.removeClassName('completed');
      this.sorting.done = 'f';
    }
    
    new Ajax.Request(this.editLink.href, {
      method: 'post',
      parameters: params,
      onComplete: this.bindOnComplete()
    });
  },
  
  recordPosition: function()
  {
    var originalPosition = this.position;
    this.taskAbove = this.findTaskAbove();
    this.taskBelow = this.findTaskBelow();
    this.position = {
      task_above: this.taskAbove && this.taskAbove.taskID(),
      task_below: this.taskBelow && this.taskBelow.taskID()
    }
    
    // Returns whether we changed anything
    return Object.toJSON(originalPosition||{}) != Object.toJSON(this.position);
  },
  
  savePosition: function()
  {
    if (this.recordPosition())
    {
      var createdAt = this.sorting.createdAt;
      var above = this.taskAbove && this.taskAbove.sorting.createdAt;
      var below = this.taskBelow && this.taskBelow.sorting.createdAt;
      if (!below) {
        var d = new Date();
        createdAt = (d.getTime() - (d.getTimezoneOffset() * 60)) * 1000;
      } else if (!above) {
        createdAt = below - 100;
      } else {
        createdAt = above + parseInt((below - above) / 2.0);
      }
      this.sorting.createdAt = createdAt;
      
      new Ajax.Request(this.editLink.href, {
        method: 'post',
        onComplete: this.bindOnComplete({}),
        parameters: this.position
      });
    }
  },
  
  bindOnComplete: function(options)
  {
    options = options || {};
    
    return function(xhr) {
      // This happens when a request is interrupted.
      if (!xhr.status || xhr.status == 0) { return; }
      
      var success = true;
      if (xhr.status == 200)
      {
        if (!xhr.responseText || xhr.responseText.indexOf('task-ajax-response') < 0)
        {
          Tasks.showError('LOGGED_OUT_ERROR');
          success = false;
        }
      }
      else if (xhr.status == 302)
      {
        Tasks.showError('LOGGED_OUT_ERROR');
        success = false;
      }
      else
      {
        Tasks.doFail(xhr);
        success = false;
      }
      
      if (success)
      {
        if (options.onSuccess) { options.onSuccess.bind(this)(xhr); }
      }
      else // fail
      {
        if (options.onFailure) { options.onFailure.bind(this)(xhr); } 
      }
      
      (options.onComplete || Prototype.emptyFunction).bind(this)(xhr);
    }.bind(this);
  },
  
  replaceRows: function(xhr)
  {
    var tbody = this.editRow.parentNode; 
    var temp = Tasks.containerFromResponse(xhr);
    var rows = temp.select('tr');

    if (rows.length < 2) {
      return false;
    }
    
    // May be adding a new task
    if (this.viewRow)
    {
      this.viewRow.remove();
    }

    var newEditRow = rows.find(function(row){ return row.hasClassName('editable'); });
    var newViewRow = rows.without(newEditRow)[0];
    
    tbody.insertBefore(newEditRow, this.editRow);
    tbody.insertBefore(newViewRow, this.editRow);
    
    this.editRow.remove();
    // Re-initialize everything.
    this.initialize(newViewRow, newEditRow);
    
    return true;
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
        body.activate();
      }
    }
    else
    {
      var input = this.editRow.select('td.' + tdClassName + '>input').first();
      if (input) { input.activate(); }
    }
  }
});