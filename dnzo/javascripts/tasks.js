var Tasks = {
  load: function(event)
  {
    Tasks.addLink = $('add');
    Event.observe(Tasks.addLink, 'click', Tasks.onClickAdd);
  },
  
  onClickAdd: function(event)
  {
    new Ajax.Request(Tasks.addLink.href, {
      method: 'get',
      onComplete: Tasks.doAdd
    })
    event.stop();
  },
  
  doAdd: function(xhr)
  {
    var temp = new Element('table');
    temp.innerHTML = xhr.responseText;
    var tbody = $('tasks_list').select('tbody')[0];
    tbody.appendChild(temp.select('tr')[0]);
    
    var project = tbody.select('input.task-project')[0];
    if (project.getValue().blank())
    {
      project.activate();
    }
    else
    {
      tbody.select('input.task-body')[0].activate();
    }
  }
}

Event.observe(window,'load',Tasks.load);