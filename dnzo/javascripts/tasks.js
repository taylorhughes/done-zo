var Tasks = {
  TASK_SAVED_EVENT: 'tasks:task_saved',
  TASK_EDITING_EVENT: 'tasks:task_editing',
  TASK_CANCEL_EDITING_EVENT: 'tasks:task_cancel_editing',
  
  load: function(event)
  {
    // Setup dropdown switcher
    var switcher = $('switcher');
    if (switcher) Event.observe(switcher, 'change', Tasks.onSwitchList);
    
    if (!Prototype.Browser.IE)
    {
      var addList = $('add_list_link');
      if (addList) Event.observe(addList, 'click', Tasks.onClickAddList);
    }
    
    Tasks.table = $('tasks_list');
    if (Tasks.table && !Tasks.table.hasClassName('archived'))
    {
      Tasks.addRow = Tasks.table.select('#add_row')[0];
      Tasks.addLink = Tasks.addRow.select('#add')[0];
    
      Event.observe(Tasks.addLink, 'click', Tasks.onClickAdd);
    
      Tasks.table.select('tr.task-row').each(function(row) {
        new TaskRow(row, null);
      });
    }
    else
    {
      // Archived list; no touchy
    }
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
  
  onClickAdd: function(event)
  {
    new Ajax.Request(Tasks.addLink.href, {
      method: 'get',
      onFailure: Tasks.doFail,
      onSuccess: Tasks.doAdd
    });
    event.stop();
  },
  
  doAdd: function(xhr)
  {
    Tasks.cancelAll();
    
    var row = Tasks.rowFromResponse(xhr);
    
    var tbody = Tasks.table.select('tbody')[0];

    tbody.removeChild(Tasks.addRow);
    tbody.appendChild(row);
    tbody.appendChild(Tasks.addRow);

    var task = new TaskRow(null, row);
    Event.observe(Tasks.table, Tasks.TASK_SAVED_EVENT, Tasks.addSaved);
    Event.observe(Tasks.table, Tasks.TASK_CANCEL_EDITING_EVENT, Tasks.addCanceled);
    
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
  }
};

var TaskRow = Class.create({
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
  
  destroy: function()
  {
    if (this.viewRow) this.viewRow.parentNode.removeChild(this.viewRow);
    if (this.editRow && this.editRow.parentNode) this.editRow.parentNode.removeChild(this.editRow);
    Event.stopObserving(Tasks.table, Tasks.TASK_EDITING_EVENT, this.boundOnOtherTaskEditing);
  },
  
  wireViewingEvents: function(row)
  {
    this.edit = row.select('.edit>a.edit')[0];
    Event.observe(this.edit, 'click', this.onClickEdit.bind(this));
    
    this.trash = row.select('.edit>a.delete')[0];
    Event.observe(this.trash, 'click', this.onClickTrash.bind(this));

    var finish = row.select('.complete')[0];
    Event.observe(finish, 'click', this.onClickComplete.bind(this));
  },
  
  wireEditingEvents: function(row)
  {
    var save = row.select('.edit>input[type=submit]')[0];
    Event.observe(save, 'click', this.onClickSave.bind(this));

    var cancelLink = row.select('.edit>a.cancel')[0];
    Event.observe(cancelLink, 'click', this.onClickCancel.bind(this));
  },
  
  isEditing: function()
  {
    return this.editRow && this.editRow.parentNode;
  },
  
  cancel: function()
  {
    this.fire(Tasks.TASK_CANCEL_EDITING_EVENT);
    
    if (this.viewRow)
    {
      this.viewRow.show();
      this.viewRow.parentNode.removeChild(this.editRow);
    }
    else
    {
      // New task; can't toggle
      this.destroy();
    }
  },
  
  onClickCancel: function(event)
  {
    this.cancel();
    event.stop();
  },
  
  onClickEdit: function(event)
  {
    this.fire(Tasks.TASK_EDITING_EVENT);
    if (this.editRow)
    {
      this.viewRow.hide();
      this.viewRow.parentNode.insertBefore(this.editRow, this.viewRow);
    }
    else
    {
      new Ajax.Request(this.edit.href, {
        method: 'get',
        onSuccess: this.doEdit.bind(this),
        onFailure: this.doFail.bind(this)
      }); 
    }
    event.stop();
  },
  doEdit: function(xhr)
  {    
    this.editRow = Tasks.rowFromResponse(xhr);
    this.viewRow.parentNode.insertBefore(this.editRow, this.viewRow);
    this.viewRow.hide();

    this.wireEditingEvents(this.editRow);
    this.activate();
  },
  
  onClickTrash: function(event)
  {
    new Ajax.Request(this.trash.href, {
      method: 'get',
      onSuccess: this.doTrash.bind(this),
      onFailure: this.doFail.bind(this)
    });
    event.stop();
  },
  doTrash: function(xhr)
  {
    this.destroy();
    Tasks.updateStatusFromResponse(xhr);
  },
  
  onClickSave: function(event)
  {
    this.editRow.up('form').request({
      onSuccess: this.doSave.bind(this),
      onFailure: this.doFail.bind(this)
    });
    
    event.stop();
  },
  doSave: function(xhr)
  {
    var tbody = this.editRow.parentNode;
    // May be adding a new task
    if (this.viewRow)
    {
      tbody.removeChild(this.viewRow);
    }
    this.viewRow = Tasks.rowFromResponse(xhr);
    this.wireViewingEvents(this.viewRow);
    
    tbody.insertBefore(this.viewRow, this.editRow);
    tbody.removeChild(this.editRow);
    this.editRow = null;
    
    this.fire(Tasks.TASK_SAVED_EVENT);
  },
  
  onClickComplete: function(event)
  {
    if (this.isEditing()) return;
    
    var check = event.element();
    var params = { 'force_complete': true };
    if (!check.checked)
    {
      params = { 'force_uncomplete': true };
    }
    
    new Ajax.Request(this.edit.href, {
      method: 'post',
      parameters: params,
      onSuccess: this.doComplete.bind(this),
      onFailure: (function(xhr){
        this.doFail();
        check.checked = !checked;
      }).bind(this)
    });
  },
  doComplete: function(xhr)
  {
    var newRow = Tasks.rowFromResponse(xhr);
    this.viewRow.className = newRow.className;
  },

  onOtherTaskEditing: function(event)
  {
    if (this.isEditing())
    {
      this.cancel();
    }
  },
  
  doFail: function(xhr)
  {
    // TODO: Do something useful when this fails.
    Tasks.doFail(xhr);
  },
  
  fire: function(eventName)
  {
    Event.fire((this.viewRow || this.editRow), eventName);
  },
  
  // Find the first empty field in the row and activate it.
  activate: function()
  {
    if (!this.editRow) return;
    
    this.editRow.select('input[type=text]').each(function(input) {
      if (input.getValue().blank())
      {
        input.activate();
        throw $break;
      }
    });
  }
});

Event.observe(window,'load',Tasks.load);