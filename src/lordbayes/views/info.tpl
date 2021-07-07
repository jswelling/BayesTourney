{% extends 'base.tpl' %}

{% block pagescripts %}
<script>
  $(function() {
    $( "#help_accordion" ).accordion();
  })
</script>
{% endblock %}

{% block content %}
<h1>About TourneyHelper</h1>

<div id="help_accordion">
<h3>What's this?</h3>
<div>
  <p>
  Say some stuff here.
  </p>
</div>
<h3>Overview</h3>
<div>
  <p>
  Say some stuff here.  
  </p>
</div>
<h3>How It Works</h3>
<div>
  <p>
  Say some stuff here.  
  </p>
</div>
<h3>The Math</h3>
<div>
  <p>
  Say some stuff here.  
  </p>
</div>
<h3>Notes</h3>
<div>
<ul>
<li>I should globally replace 'tourneys' with 'tournies'.
</ul>
</div>
</div>

{% endblock %}
