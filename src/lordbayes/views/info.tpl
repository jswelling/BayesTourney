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
<h3>Editing Tips</h3>
<div>
<p>
Click on a row to edit it.  Once a row is being edited, you can save
the new values with the 'Enter' key or cancel the edit with the 'Esc(ape)'
key.  The escape key won't work in multi-line fields like 'Notes', so to
edit a note you must type in that field, then <em>select a different
field</em> and use the 'Enter' key to save your edits.
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
