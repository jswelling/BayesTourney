<!doctype html>
 
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Tourney Helper</title>
  <link rel="stylesheet" href="/static/jquery-ui-1.10.2/themes/base/jquery-ui.css" />
  <link rel="stylesheet" href="/static/jqGrid-4.5.2/css/ui.jqgrid.css" />
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
  $(function() {
    $( "#tabs" ).tabs({
      beforeLoad: function( event, ui ) {
        ui.jqXHR.error(function() {
          ui.panel.html(
            "Couldn't load this tab. We'll try to fix this as soon as possible. " +
            "If this wouldn't be a demo." );
        });
      }
    });
{% if curTab is not none %}
    $("#tabs").tabs({ active: {{curTab}} });
{% endif %}
  });
  </script>
</head>
<body>

<h1>Tourney Helper</h1>
 
<div id="tabs">
  <ul>
  	<li><a href="ajax/tourneys">Tourneys</a></li>
    <li><a href="ajax/entrants">Entrants</a></li>
    <li><a href="ajax/bouts">Bouts</a></li>
    <li><a href="ajax/horserace">Horse Race</a></li>
    <li><a href="ajax/help">Help</a></li>
  </ul>
</div>
 
 
</body>
</html>
