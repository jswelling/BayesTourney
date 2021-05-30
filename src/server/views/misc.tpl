<h1>Miscellaneous</h1>

<label for="sel_misc_tournament">Which Tournament?</label>
<select id="sel_misc_tournament">
<option value=-1>All</option>
%	tourneyList = db.query(Tourney)
%    pairs = [((t.tourneyId,t.name)) for t in tourneyList]
%    pairs.sort()
%    for thisId,name in pairs:
<option value={{thisId}}>{{name}}</option>
%    end
</select>

<button id="misc_download_btn">Download!</button>

<script>
var selTourney = $('#sel_horserace_tournament');
selTourney.select();
var dLBtn = $('#misc_download_btn');
dLBtn.button().click( function()
{ 
  $.get('ajax/misc_download', {tourney: selTourney.val()})
  .done( function(data) {
    alert('done');
  })
  .fail(function(jqxhr, textStatus, error) {
		alert('Error: '+jqxhr.responseText);
  });
});

</script>
