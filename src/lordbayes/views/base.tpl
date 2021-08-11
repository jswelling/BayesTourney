<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
{% from "macros.html" import nav_link with context %}
<html lang="en">
  <head>
    <meta charset="utf-8" />

    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.form/4.3.0/jquery.form.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js"></script>
    <script crossorigin="anonymous"
            src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js"
            integrity="sha256-98vAGjEDGN79TjHkYWVD4s87rvWkdWLHPs5MC3FvFX4="></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.1.3/js/bootstrap.min.js"></script>
    <script>
      $.jgrid = $.jgrid || {};
      $.jgrid.no_legacy_api = true;
    </script>
    <script crossorigin="anonymous"
            src="https://cdnjs.cloudflare.com/ajax/libs/free-jqgrid/4.15.5/jquery.jqgrid.min.js"
            integrity="sha256-ELi2cs17gL2MqNzkRkogxZsVLmL+oWfeVOwZQLcp8ek=">
    </script>

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

    <link rel="stylesheet"
	  href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/themes/redmond/jquery-ui.min.css"/>
    <link rel="stylesheet"
	  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"/>
    <link href="http://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap.min.css"
	  rel="stylesheet" media="screen" />
    <link rel="stylesheet"
	  href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/css/bootstrap-theme.min.css"/>
    <link rel="stylesheet"
	  href="https://cdnjs.cloudflare.com/ajax/libs/free-jqgrid/4.15.5/css/ui.jqgrid.min.css"/>
    <link rel="apple-touch-icon" sizes="180x180"
	  href="{{ url_for('static', filename='apple-touch-icon.png') }}" />
    <link rel="icon" type="image/png"
	  sizes="32x32" href="{{ url_for('static', filename='favicon-32x32.png') }}" />
    <link rel="icon" type="image/png" sizes="16x16"
	  href="{{ url_for('static', filename='favicon-16x16.png') }}" />
    <link rel="manifest" href="{{ url_for('static', filename='manifest.json') }}" />
  </head>
  <body>
    <nav class="navbar navbar-inverse" role="navigation">
      <div class="container-fluid">
	<!--
	    <h1>{% block heading %}{% endblock %} - Tourney Helper Heading</h1>
	    -->
	<div class="navbar-header">
	  <button type="button" class="navbar-toggle" data-toggle="collapse"
		  data-target="#bs-example-navbar-collapse-1">
	    <span class="sr-only">Toggle navigation</span>
	    <span class="icon-bar"></span>
	    <span class="icon-bar"></span>
	    <span class="icon-bar"></span>
	  </button>
	  <a class="navbar-brand" href="/">LordBayesTourney</a>
	</div>

	<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
	  <ul class="nav navbar-nav">
	    {{ nav_link('tourneys', 'Tourneys') }}
	    {{ nav_link('entrants', 'Entrants') }}
	    {{ nav_link('bouts', 'Bouts') }}
	    {{ nav_link('horserace', 'Horserace') }}
	  </ul>
	  <!--
	      <form class="navbar-form navbar-left" role="search">
		<div class="form-group">
		  <input type="text" class="form-control" placeholder="Search"/>
		</div>
		<button type="submit" class="btn btn-default">Submit</button>
	      </form>
	      -->
	  <ul class="nav navbar-nav navbar-right">
	    {{ nav_link('help', 'Help') }}
	    <li class="dropdown">
	      <a href="#" class="dropdown-toggle" data-toggle="dropdown">
		Misc <b class="caret"></b></a>
	      <ul class="dropdown-menu">
		{{ nav_link('site_map', 'Site Map') }}
		<!--
		<li><a href="#">Site Map</a></li>
		<li><a href="#">Another action</a></li>
		-->
	      </ul>
	    </li>
	    {% if g.user %}
	    <li class="navbar-text"><span>{{ g.user['username'] }}</span></li>
	    <li><a href="{{ url_for('auth.logout') }}">Log Out</a></li>
	    {% else %}
	    <li><a href="{{ url_for('auth.register') }}">Register</a></li>
	    <li><a href="{{ url_for('auth.login') }}">Log In</a></li>
	    {% endif %}
	  </ul>
	</div><!-- /.navbar-collapse -->
      </div><!-- /.container-fluid -->
    </nav>
    <section class="container">
      <header>
	{% block header %}{% endblock %}
      </header>
      {% for message in get_flashed_messages() %}
      <div class="flash">{{ message }}</div>
      {% endfor %}
      <br>
	{% block content %}
	{% endblock %}
      </br>
    </section>
  </body>
</html>
