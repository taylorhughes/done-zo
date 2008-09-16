var Tasks = {
  TASK_SAVED_EVENT: 'tasks:task_saved',
  TASK_EDITING_EVENT: 'tasks:task_editing',
  TASK_CANCEL_EDITING_EVENT: 'tasks:task_cancel_editing',
  
  load: function(event)
  {
    Tasks.table = $('tasks_list');
    Tasks.addRow = Tasks.table.select('#add_row')[0];
    Tasks.addLink = Tasks.addRow.select('#add')[0];
    
    Event.observe(Tasks.addLink, 'click', Tasks.onClickAdd);
    
    Tasks.table.select('tr.task-row').each(function(row) {
      new TaskRow(row);
    });
    
    Event.observe('switcher', 'change', Tasks.onSwitchList);
  },
  
  onClickAdd: function(event)
  {
    new Ajax.Request(Tasks.addLink.href, {
      method: 'get',
      onFailure: Tasks.doFail,
      onSuccess: Tasks.doAdd
    });
    event.stop();
  
    Tasks.cancelAll();
  },
  
  onSwitchList: function(event)
  {
    document.location.href = $F(event.element());
  },
  
  cancelAll: function()
  {
    Event.fire(Tasks.table, Tasks.TASK_EDITING_EVENT);
  },
  
  loadStatus: function(container)
  {
    var status = container.select("#status");
    if (status.length > 0)
    {
      status = status[0];
      
      var existingStatus = $("status");
      if (existingStatus)
      {
        existingStatus.innerHTML = status.innerHTML;
        existingStatus.show();
      }
      else
      {
        Tasks.table.up('div').appendChild(status);
      }
    }
  },
  
  updateStatusFromResponse: function(xhr)
  {
    Tasks.loadStatus(Tasks.containerFromResponse(xhr));
  },
  
  containerFromResponse: function(xhr)
  {
    var temp = new Element('div');
    temp.innerHTML = xhr.responseText;
    return temp;
  },
  
  rowFromResponse: function(xhr)
  {
    var temp = Tasks.containerFromResponse(xhr);
    var row = temp.select('tr');
    if (row.length > 0) 
    {
      return row[0];
    }
    return null;
  },
  
  doFail: function(xhr)
  {
    alert("Ruh roh! Something went wrong. Please let us know what happened!");
  },
  
  doAdd: function(xhr)
  {
    var row = Tasks.rowFromResponse(xhr);
    
    var tbody = Tasks.table.select('tbody')[0];
    tbody.removeChild(Tasks.addRow);
    tbody.appendChild(row);
    tbody.appendChild(Tasks.addRow);

    var task = new TaskRow(row);
    Event.observe(task.row, Tasks.TASK_SAVED_EVENT, Tasks.addSaved.bind(this));
    Event.observe(task.row, Tasks.TASK_CANCEL_EDITING_EVENT, Tasks.addCanceled.bind(this));
    
    Tasks.addRow.hide();
    task.activate();
  },
  
  addCanceled: function(event)
  {
    Tasks.addRow.show();
    event.stop();
  },
  
  addSaved: function(event)
  {
    Tasks.onClickAdd(event);
  }
};

var TaskRow = Class.create({
  initialize: function(row)
  {
    this.row = row;
    this.setupEvents();
    
    // Need to keep this around so we can unobserve it later in destroy()
    this.boundOnOtherTaskEditing = this.onOtherTaskEditing.bind(this);
    Event.observe(document, Tasks.TASK_EDITING_EVENT, this.boundOnOtherTaskEditing);
  },
  
  destroy: function()
  {
    this.row.parentNode.removeChild(this.row);
    Event.stopObserving(document, Tasks.TASK_EDITING_EVENT, this.boundOnOtherTaskEditing);
  },
  
  setupEvents: function()
  {
    var edit = this.row.select('.edit>a.edit');
    if (edit.length > 0)
    {
      this.edit = edit[0];
      Event.observe(this.edit, 'click', this.onClickEdit.bind(this));
    }
    
    var trash = this.row.select('.edit>a.delete');
    if (trash.length > 0)
    {
      this.trash = trash[0];
      Event.observe(this.trash, 'click', this.onClickTrash.bind(this));
    }
    
    var save = this.row.select('.edit>input[type=submit]');
    if (save.length > 0)
    {
      this.save = save[0];
      Event.observe(this.save, 'click', this.onClickSave.bind(this));
      this.cancelLink = this.row.select('.edit>a.cancel')[0];
      Event.observe(this.cancelLink, 'click', this.onClickCancel.bind(this));
    }
    
    var complete = this.row.select('.complete');
    if (complete.length > 0 && !complete[0].hasClassName('editing'))
    {
      this.complete = complete[0];
      Event.observe(this.complete, 'click', this.onClickComplete.bind(this));
    }
  },
  
  isEditing: function()
  {
    return this.row.hasClassName('editable');
  },
  
  cancel: function()
  {
    if (this.restore)
    {
      this.loadRestore();
      this.setupEvents();
    }
    else
    {
      // New task.
      this.destroy();
    }
    
    this.fire(Tasks.TASK_CANCEL_EDITING_EVENT);
  },
  
  onClickCancel: function(event)
  {
    this.cancel();
    event.stop();
  },
  
  onClickEdit: function(event)
  {
    this.saveRestore();
    
    new Ajax.Request(this.edit.href, {
      method: 'get',
      onSuccess: this.doEdit.bind(this),
      onFailure: this.doFail.bind(this)
    });
    event.stop();
  },
  
  onClickTrash: function(event)
  {
    var row = event.element().up('tr');
    new Ajax.Request(this.trash.href, {
      method: 'get',
      onSuccess: (function(xhr){ this.doTrash(xhr, row); }).bind(this),
      onFailure: this.doFail.bind(this)
    });
    event.stop();
  },
  
  onClickSave: function(event)
  {
    this.row.up('form').request({
      onSuccess: this.doSave.bind(this),
      onFailure: this.doFail.bind(this)
    });
    
    event.stop();
  },
  
  onClickComplete: function(event)
  {
    if (this.isEditing()) return;
    
    var checked = event.element().checked;
    var params = { 'force_complete': true };
    if (!checked)
    {
      params = { 'force_uncomplete': true };
    }
    
    new Ajax.Request(this.edit.href, {
      method: 'post',
      parameters: params,
      onSuccess: this.doLoad.bind(this),
      onFailure: (function(xhr){
        this.doFail();
        event.element().checked = !checked;
      }).bind(this)
    });
  },

  onOtherTaskEditing: function(event)
  {
    if (this.isEditing())
    {
      this.cancel();
    }
  },
  
  doEdit: function(xhr)
  {
    this.fire(Tasks.TASK_EDITING_EVENT);
    this.doLoad(xhr);
  },
  
  doTrash: function(xhr, row)
  {
    row.hide();
    Tasks.updateStatusFromResponse(xhr);
  },
  
  doSave: function(xhr)
  {
    this.doLoad(xhr);
    this.restore = null;
    
    this.fire(Tasks.TASK_SAVED_EVENT);
  },
  
  doLoad: function(xhr)
  {
    var row = Tasks.rowFromResponse(xhr);
    TaskRow.restoreFields(row, this.row);
    
    this.setupEvents();
    this.activate();
  },
  
  doFail: function(xhr)
  {
    // TODO: Do something useful when this fails.
    Tasks.doFail(xhr);
  },
  
  saveRestore: function()
  {
    this.restore = {};
    TaskRow.restoreFields(this.row, this.restore);
  },
  
  loadRestore: function()
  {
    TaskRow.restoreFields(this.restore, this.row);
  },
  
  fire: function(eventName)
  {
    Event.fire(this.row,eventName);
  },
  
  // Find the first empty field in the row and activate it.
  activate: function()
  {
    this.row.select('input[type=text]').each(function(input) {
      if (input.getValue().blank())
      {
        input.activate();
        throw $break;
      }
    });
  }
});
TaskRow.restoreFields = function(from, to)
{
  ['className', 'innerHTML'].each(function(field){
    to[field] = from[field];
  });
}

Event.observe(window,'load',Tasks.load);