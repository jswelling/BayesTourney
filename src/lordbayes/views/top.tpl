{% extends 'base.tpl' %}

{% block pagescripts %}
<script>
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
{% endblock %}

{% block title %}
Main Page
{% endblock %}

{% block heading %}
Main Page
{% endblock %}

{% block header %}
{% endblock %}

{% block content %}

<div id="tabs">
  <ul>
    <li><a href="ajax/tourneys">Tourneys</a></li>
    <li><a href="ajax/entrants">Entrants</a></li>
    <li><a href="ajax/bouts">Bouts</a></li>
    <li><a href="ajax/horserace">Horse Race</a></li>
    <li><a href="ajax/help">Help</a></li>
  </ul>
</div>
 
{% endblock %}
