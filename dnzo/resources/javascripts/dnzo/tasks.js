var Tasks = {
  TASK_SAVED_EVENT: 'tasks:task_saved',
  TASK_EDITING_EVENT: 'tasks:task_editing',
  TASK_CANCEL_EDITING_EVENT: 'tasks:task_cancel_editing',
  
  // events used in sorting
  TASK_IDENTIFY_BY_ROW_EVENT: 'tasks:task_identify',
  TASK_REQUEST_SORT_EVENT: 'tasks:request_sort',
  
  // events for when the table becomes draggable
  TASKS_DRAGGABLE_EVENT: 'tasks:draggable',
  TASKS_NOT_DRAGGABLE_EVENT: 'tasks:not_draggable',
  
  
  load: function(event)
  {
    Tasks.table = $('tasks_list');
    if (!Tasks.table || Tasks.table.hasClassName('archived')) { return; }
    
    new ModalDialog.Ajax($('add_list'), {
      afterShown: function() {
        var newListName = $('new_list_name');
        if (newListName) { newListName.activate(); }
      }
    });
    
    Tasks.addRow = $('add_row');
    
    Tasks.tasksForm = $('tasks_form');
    Tasks.newTaskTableHTML = Tasks.tasksForm.innerHTML;
  
    Tasks.addRow.observe('click', Tasks.onClickAddTask);
    
    Tasks.wireSortingEvents();
  
    var rows = Tasks.table.select('tr.task-row');
    for (var i = 0; i < rows.length; i += 2)
    {
      // NOTE: This makes us depdendent on the order that these
      //       rows are output. That is not good, but this is fast.
      new TaskRow(rows[i + 1], rows[i]);
    }
    
    Event.observe(document, 'dblclick', Tasks.onDoubleClickBody);
    Event.observe(document, 'keypress', Tasks.onKeyPress);
    
    Tasks.wireHistory();
  },
  
  wireSortingEvents: function()
  {
    Tasks.table.select('th>a').each(function(sortingLink) {
      sortingLink.observe('click',Tasks.onClickSort);
    });
  },
  
  wireHistory: function()
  {
    Tasks.onHistoryChange();
    History.Observer.observe('all', Tasks.onHistoryChange);
    History.Observer.start();
  },
  
  addHistoryEvent: function(data)
  {
    History.setMultiple(data);
  },
  
  draggable: function()
  {
    return Tasks.table.hasClassName('draggable');
  },
  
  onDoubleClickBody: function(event)
  {
    Tasks.cancelAll();
  },
  
  onKeyPress: function(event)
  {
    switch(event.charCode)
    {
      case 65:
      case 97:
        var element = event.findElement();
        if (!element.match('input') && !element.match('select'))
        {
          Tasks.onClickAddTask(event);
        }
    }
  },
  
  onHistoryChange: function(name)
  {
    Tasks.sort(History.get('order'), History.get('descending'));
  },
  
  onClickSort: function(event)
  {
    event.stop();
    
    var link = event.element();
    link = link.match('a') ? link : link.up('a');
    var headerCell = link.up('th');
    
    var column = link.href.match(/order=([\w_]+)/)[1];
    var descending = false;
        
    if (headerCell.match('.sorted.descending'))
    {      
      column = null;
    }
    else if (headerCell.match('.sorted'))
    {
      descending = true;
    }
    
    var data = { order: column || "" };
    if (column && descending) {
      data.descending = true;
    } else {
      data.descending = null;
    }
    Tasks.addHistoryEvent(data);
    
    Tasks.sort(column,descending);
  },
  
  sort: function(column,descending)
  {    
    Tasks.cancelAll();
    
    Tasks.table.select('th').each(function(cell){
      ['sorted','descending'].each(function(c){cell.removeClassName(c)});
      if (cell.hasClassName(column)) {
        cell.addClassName('sorted');
        if (descending) {
          cell.addClassName('descending');
        }
      }
    });
    
    // TaskRows that are listening add themselves to the event.memo array
    var rows = Event.fire(Tasks.table, Tasks.TASK_REQUEST_SORT_EVENT, []).memo;
    
    // Then we sort them
    rows.sort(function(a,b){
      return a.compareTo(b,column,descending);
    });
    
    rows.each(function(row){
      row.removeRows();
      row.addRowsBefore(Tasks.addRow);
    });
    
    if (column && Tasks.table.hasClassName('draggable')) {
      Event.fire(Tasks.table,Tasks.TASKS_NOT_DRAGGABLE_EVENT);
      Tasks.table.removeClassName('draggable');
    } else if (!column && !Tasks.table.hasClassName('draggable')) {
      Event.fire(Tasks.table,Tasks.TASKS_DRAGGABLE_EVENT);
      Tasks.table.addClassName('draggable');
    }
  },
  
  taskFromRow: function(row)
  {
    // This fires an event asking for the TaskRow object that has this row to identify itself
    var e = Event.fire(Tasks.table, Tasks.TASK_IDENTIFY_BY_ROW_EVENT, { row: row });
    return e.memo.task;
  },
  
  onClickAddTask: function(event)
  {
    event.stop();
    
    Tasks.cancelAll();
    // event.memo is set to be the task that was just added by the TaskRow's
    // save method, which fires a TASK_SAVED_EVENT using its editRow as memo
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
  
  doAddNewTask: function(row, existingTask, activateClassName)
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
    task.activate(activateClassName);
  },
  
  cancelAll: function()
  {
    Event.fire(Tasks.table, Tasks.TASK_EDITING_EVENT);
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
  
  showError: function(message)
  {
    if (typeof message == 'undefined')
    {
      message = 'DEFAULT_ERROR';
    }
    
    var errorContainer = new Element('div', { className: 'error_dialog dialog_content' });
    
    var h2 = new Element('h2');
    h2.innerHTML = 'Whoops!';
    errorContainer.appendChild(h2);
    var ul = new Element('ul');
    errorContainer.appendChild(ul);
    
    DNZO.Messages[message].split("\n").each(function(str){
      var li = new Element('li');
      li.innerHTML = str;
      ul.appendChild(li);
    });
    var buttons = new Element('li', { className: 'buttons' });
    buttons.appendChild(new Element('input', { type: 'submit', value: 'OK', className: 'hide_dialog' }));
    ul.appendChild(buttons);
    
    (new ModalDialog(errorContainer)).show();
  },
  
  doFail: function(xhr)
  {
    Tasks.showError();
  }
};

Event.observe(window,'load',Tasks.load);
