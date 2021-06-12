<h1>Miscellaneous</h1>

<label for="sel_misc_tournament">Which Tournament?</label>
<select id="sel_misc_tournament">
<option value=-1>All</option>
{% for id, name in tourneyDict | dictsort %}
<option value={{id}}>{{name}}</option>
{% endfor %}
</select>

<a id="download_bouts_link" href="/ajax/misc_download?tourney=-1">Download bouts as .tsv</a>
<script>
var selMiscTourney = $('#sel_misc_tournament');
selMiscTourney.select().change( function()
{
  $('#download_bouts_link').attr('href', '/ajax/misc_download?tourney=' + selMiscTourney.val());
});

</script>
