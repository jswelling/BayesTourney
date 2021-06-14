<!doctype html lang=en>

  <meta charset="utf-8" />
  <script src="/static/jquery-1.10.1.min.js"></script>
  <script src="/static/jquery-ui-1.10.2/ui/jquery-ui.js"></script>
  <script type="text/javascript" src="/static/jqGrid-4.5.2/js/grid.locale-en.js"></script>
  <script type="text/javascript" src="/static/jqGrid-4.5.2/js/jquery.jqGrid.min.js"></script>

  <script>
  /*
   * Magic to make AJAX ops like $.getJSON send the same cookies as normal fetches
   */
   $(document).ajaxSend(function (event, xhr, settings) {
       settings.xhrFields = {
           withCredentials: true
       };
   });
  </script>
{% block pagescripts %}{% endblock %}
  
<title>{% block title %}{% endblock %} - Tourney Helper</title>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  <link rel="stylesheet" href="/static/jquery-ui-1.10.2/themes/base/jquery-ui.css" />
  <link rel="stylesheet" href="/static/jqGrid-4.5.2/css/ui.jqgrid.css" />
<nav>
  <h1>{% block heading %}{% endblock %} - Tourney Helper</h1>
 <ul>
    {% if g.user %}
      <li><span>{{ g.user['username'] }}</span>
      <li><a href="{{ url_for('auth.logout') }}">Log Out</a>
    {% else %}
      <li><a href="{{ url_for('auth.register') }}">Register</a>
      <li><a href="{{ url_for('auth.login') }}">Log In</a>
    {% endif %}
  </ul>
</nav>
<section class="content">
  <header>
    {% block header %}{% endblock %}
  </header>
  {% for message in get_flashed_messages() %}
    <div class="flash">{{ message }}</div>
  {% endfor %}
  {% block content %}{% endblock %}
</section>
