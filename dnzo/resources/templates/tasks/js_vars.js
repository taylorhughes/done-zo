  <script type="text/javascript">
    var DNZO = {
      timezoneInfo: { 
        offset:    parseInt("{{ user.timezone_offset_mins }}") || 0,
        updateUrl: "{% url tasks.views.transparent_settings %}"
      },
      projects: [{% for project in user.mru_projects %}"{{ project|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}]
    };
  </script>