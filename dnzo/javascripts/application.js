var DNZO = {
  load: function(event)
  {
    // Setup dropdown switcher
    var switcher = $('switcher');
    if (switcher) Event.observe(switcher, 'change', DNZO.onSwitchList); 
  },
  
  onSwitchList: function(event)
  {
    document.location.href = $F(event.element());
  }  
};

Event.observe(window,'load',DNZO.load);