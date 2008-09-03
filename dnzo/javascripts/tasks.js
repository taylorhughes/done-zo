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
  
  cancelAll: function()
  {
    Event.fire(Tasks.table, Tasks.TASK_EDITING_EVENT);
  },
  
  doFail: function(xhr)
  {
    alert("Ruh roh! Something went wrong. Please let us know what happened!");
  },
  
  cancelAdd: function(event)
  {
    Tasks.addRow.show();
    event.stop();
  },
  
  doAdd: function(xhr)
  {
    var temp = new Element('table');
    temp.innerHTML = xhr.responseText;
    
    var tbody = Tasks.table.select('tbody')[0];
    var row = temp.select('tr')[0];
    tbody.removeChild(Tasks.addRow);
    tbody.appendChild(row);
    tbody.appendChild(Tasks.addRow);

    var task = new TaskRow(row);
    Event.observe(task.row, Tasks.TASK_SAVED_EVENT, Tasks.cancelAdd.bind(this));
    Event.observe(task.row, Tasks.TASK_CANCEL_EDITING_EVENT, Tasks.cancelAdd.bind(this));
    
    Tasks.addRow.hide();
    task.activate();
  }
};

var TaskRow = Class.create({
  initialize: function(row)
  {
    this.row = row;
    this.setupEvents();
    
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
  
  onOtherTaskEditing: function(event)
  {
    if (this.isEditing())
    {
      this.cancel();
    }
  },
  
  onClickEdit: function(event)
  {
    this.saveRestore();
    
    new Ajax.Request(this.edit.href, {
      method: 'get',
      onSuccess: (function(xhr){
        this.fire(Tasks.TASK_EDITING_EVENT);
        this.doLoad(xhr);
      }).bind(this),
      onFailure: this.doFail.bind(this)
    });
    event.stop();
  },
  
  onClickSave: function(event)
  {
    this.row.up('form').request({
      onSuccess: (function(xhr) {
        this.doLoad(xhr);
        this.restore = null;
      }).bind(this),
      onFailure: this.doFail.bind(this)
    });
    
    event.stop();
    
    this.fire(Tasks.TASK_SAVED_EVENT);
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
  
  saveRestore: function()
  {
    this.restore = {};
    TaskRow.restoreFields(this.row, this.restore);
  },
  
  loadRestore: function()
  {
    TaskRow.restoreFields(this.restore, this.row);
  },
  
  doLoad: function(xhr)
  {
    var temp = new Element('table');
    temp.innerHTML = xhr.responseText;
    temp = temp.select('tr')[0];
    
    TaskRow.restoreFields(temp, this.row);
    
    this.setupEvents();
    this.activate();
  },
  
  doFail: function(xhr)
  {
    // TODO: Do something useful when this fails.
    Tasks.doFail(xhr);
  },
  
  fire: function(eventName)
  {
    Event.fire(this.row,eventName);
  },
  
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