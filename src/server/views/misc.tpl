<h1>Miscellaneous</h1>

<label for="sel_misc_tournament">Which Tournament?</label>
<select id="sel_misc_tournament">
<option value=-1>All</option>
{% for id, name in tourneyDict | dictsort %}
<option value={{id}}>{{name}}</option>
{% endfor %}
</select>

<button id="misc_download_btn">Download!</button>

<script>
var selMiscTourney = $('#sel_misc_tournament');
selMiscTourney.select();
var dLBtn = $('#misc_download_btn');
dLBtn.button().click( function()
{
  $.get('ajax/misc_download', {tourney: selMiscTourney.val()})
  .done( function(data) {
  })
  .fail(function(jqxhr, textStatus, error) {
		alert('Error: '+jqxhr.responseText);
  });
});

</script>
