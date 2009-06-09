<script type="text/javascript">
  var DNZO = {
    timezoneInfo: { 
      offset:    parseInt("{{ user.timezone_offset_mins }}") || 0,
      updateUrl: "{% dnzo_url transparent_settings %}"
    },
    projects: [{% for project in user.mru_projects %}"{{ project|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}],
    contexts: [{% for context in user.mru_contexts %}"@{{ context|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}]
  };
  DNZO.Messages = {
    DEFAULT_ERROR:
      "Ruh roh! Something went wrong, and we couldn't perform " + 
      "the action you requested. Please refresh the page and try again.\n" + 
      "If your problems persist, please contact us and let us know what's wrong.",
    TASKS_LIMIT_ERROR:
      "There was a problem saving your task.\n" + 
      "There is a limit on the number of unfinished tasks &mdash; " +
      "if you have several pages of unfinished tasks, " + 
      "try finishing or deleting one before adding a new one again.\n" +
      "If this problem persists, please contact us.",
    LOGGED_OUT_ERROR:
      "There was a problem saving your task.\n" +
      "You may have been logged out. Please reload the page to try again."
  };
</script>