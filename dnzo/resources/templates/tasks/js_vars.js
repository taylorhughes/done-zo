  <script type="text/javascript">
    var TimezoneInfo = { 
      offset:    parseInt("{{ user.timezone_offset_mins }}") || 0,
      updateUrl: "{% url tasks.views.transparent_settings %}"
    };
    
    var Projects = [{% for project in user.mru_projects %}"{{ project|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}];
  </script>