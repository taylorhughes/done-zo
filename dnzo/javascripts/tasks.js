var Tasks = {
  TASK_SAVED_EVENT: 'tasks:task_saved',
  TASK_EDITING_EVENT: 'tasks:task_editing',
  TASK_CANCEL_EDITING_EVENT: 'tasks:task_cancel_editing',
  
  HIDE_STATUS_DELAY: 15, // seconds
  
  load: function(event)
  {
    if (!Prototype.Browser.IE)
    {
      var addList = $('add_list_link');
      if (addList) Event.observe(addList, 'click', Tasks.onClickAddList);
    }
    
    Tasks.table = $('tasks_list');
    if (! Tasks.table || Tasks.table.hasClassName('archived'))
    {
      return;
    }
    
    Tasks.addRow = Tasks.table.select('#add_row')[0];
    Tasks.addLink = Tasks.addRow.select('#add')[0];
    
    Tasks.tasksForm = $('tasks_form');
    Tasks.newTaskTableHTML = Tasks.tasksForm.innerHTML;
  
    Event.observe(Tasks.addLink, 'click', Tasks.onClickAddTask);
  
    var rows = Tasks.table.select('tr.task-row');
    for (var i = 0; i < rows.length; i += 2)
    {
      // NOTE: This makes us depdendent on the order that these
      //       rows are output. That is not good, but this is fast.
      new TaskRow(rows[i + 1], rows[i]);
    }
    
    Tasks.setHideStatus();
  },
  
  // Add new list
  onClickAddList: function(event)
  {
    event.stop();
    
    var form = $$("form#add_list");
    if (form.length == 0) return;
    form = form[0];
    
    var name = prompt("Enter a name for your new list:");
    
    form.select('input[type=text]')[0].setValue(name);
    form.submit();
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
      var newInputs = row.select('input[type=text]');
      var oldInputs = existingTask.select('input[type=text]');
      newInputs[0].setValue(oldInputs[0].getValue());
      newInputs[2].setValue(oldInputs[2].getValue());
    }

    var task = new TaskRow(null, row);
    Event.observe(Tasks.table, Tasks.TASK_SAVED_EVENT, Tasks.addSaved);
    Event.observe(row, Tasks.TASK_CANCEL_EDITING_EVENT, Tasks.addCanceled);
    
    Tasks.addRow.hide();
    task.activate();
  },
  
  cancelAll: function()
  {
    Event.fire(Tasks.table, Tasks.TASK_EDITING_EVENT);
  },
  
  loadStatus: function(container)
  {
    var status = container.select("#status");
    if (status.length == 0)
    {
      return;
    }
    
    status = status[0];
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
      duration: 0.25,
      afterFinish: function() {
        new Effect.BlindUp(status, { duration: 0.25 });
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
      duration: 0.25,
      afterFinish: function() {
        new Effect.Parallel(subeffects, { duration: 0.25 });
      }
    });
  },
  
  updateStatusFromResponse: function(xhr)
  {
    Tasks.loadStatus(Tasks.containerFromResponse(xhr));
  },
  
  saveTask: function(row, options)
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
    duplicateBySelector(row, Tasks.tasksForm, 'input[type=hidden]');
    var chk = 'input[type=checkbox]';
    Tasks.tasksForm.select(chk)[0].checked = row.select(chk)[0].checked;
    Tasks.tasksForm.request(options);
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
    if (viewRow)
    {
      this.viewRow = viewRow;
      this.wireViewingEvents(this.viewRow);
    }
    if (editRow)
    {
      this.editRow = editRow;
      this.wireEditingEvents(this.editRow);
    }
    
    // Need to keep this around so we can unobserve it later in destroy()
    this.boundOnOtherTaskEditing = this.onOtherTaskEditing.bind(this);
    Event.observe(Tasks.table, Tasks.TASK_EDITING_EVENT, this.boundOnOtherTaskEditing);
  },
  
  wireViewingEvents: function(row)
  {
    this.editLink = row.select('.edit>a.edit')[0];
    Event.observe(this.editLink, 'click', this.onClickEdit.bind(this));

    this.trashcan = row.select('.edit>a.delete')[0];
    Event.observe(this.trashcan, 'click', this.onClickTrash.bind(this));

    var finish = row.select('.complete')[0];
    Event.observe(finish, 'click', this.onClickComplete.bind(this));
  },
  
  wireEditingEvents: function(row)
  {
    var save = row.select('.edit>input[type=submit]')[0];
    Event.observe(save, 'click', this.onClickSave.bind(this));
    
    Event.observe(row, 'keyup', this.onKeyUp.bind(this));

    this.cancelLink = row.select('.edit>a.cancel')[0];
    this.boundOnClickCancel = this.onClickCancel.bind(this);
    Event.observe(this.cancelLink, 'click', this.boundOnClickCancel);
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
  
  fire: function(eventName, memo)
  {
    Event.fire((this.viewRow || this.editRow), eventName, memo);
  },
  
  /*** EVENT HANDLERS ***/
  
  onClickEdit: function(event)
  {
    this.edit();
    event.stop();
  },
  
  onClickCancel: function(event)
  {
    this.cancel();
    event.stop();
  },
  
  onClickTrash: function(event)
  {
    this.trash();
    event.stop();
  },
  
  onClickSave: function(event)
  {
    // pointerX and pointerY are zero if it was clicked by, for
    // example, hitting return as opposed to actually clicking it.
    if (event.pointerX() != 0 || event.pointerY() != 0)
    {
      this.save();
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
  
  /*** ACTIONS ***/

  edit: function()
  {
    this.fire(Tasks.TASK_EDITING_EVENT);
    
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
      
      Tasks.saveTask(this.editRow,{
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
  
  activate: function()
  {
    if (!this.editRow) return;
    
    var body = this.editRow.select('input.task-body').first();
    var project = this.editRow.select('input.task-project').first();
    
    if (!body || !project) { return; }
    
    if (body.getValue().blank() && project.getValue().blank()) { 
      project.activate();
    }
    else
    {
      body.activate();
    }    
  }
});

Event.observe(window,'load',Tasks.load);