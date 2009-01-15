Migrations = {
  load: function(event)
  {
    Migrations.link = $('migration_link');
    if (!Migrations.link) { return; }
    
    Migrations.lastKey = null;
    Migrations.setupUpdate();   
  },
  
  setupUpdate: function()
  {
    params = {};
    if (Migrations.lastKey)
    {
      params.start = Migrations.lastKey;
    }
    
    new Ajax.Request(Migrations.link.href, {
      parameters: params,
      method: 'post',
      onSuccess: Migrations.doUpdate,
      onFailure: Migrations.doFail
    })
  },
  
  doUpdate: function(xhr)
  {
    var temp = new Element('ul');
    temp.innerHTML += xhr.responseText;
    
    var lastKey = temp.select('span.last-key').first();
    var totalMigrated = temp.select('span.total-migrated').first();
    Migrations.lastKey = lastKey && lastKey.innerHTML;
    
    $('progress').appendChild(temp.select('li').first());
    
    if (parseInt(totalMigrated.innerHTML) > 0)
    {
      Migrations.setupUpdate();
    }
  },
  
  doFail: function(xhr)
  {
    alert("Ruh roh! Something went wrong. Fuck.");
  }
}

Event.observe(window, 'load', Migrations.load);