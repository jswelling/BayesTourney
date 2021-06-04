<h1>Horserace</h1>

<label for="sel_horserace_tournament">Which Tournament?</label>
<select id="sel_horserace_tournament">
<option value=-1>All</option>
{% for id, name in tourneyDict | dictsort %}
<option value={{id}}>{{name}}</option>
{% endfor %}
</select>

<table id="horserace_table"></table>
<div id="horserace_pager"></div>
<button id="horserace_go_btn">Go!</button>

<script>
var selTourney = $('#sel_horserace_tournament');
selTourney.select().change( function()
{
	$('#horserace_table').trigger('reloadGrid');
});
var goBtn = $('#horserace_go_btn');
goBtn.button().click( function()
{ 
  $.getJSON('json/horserace_go.json', {tourney: selTourney.val()})
  .done( function(data) {
    alert('done');
    alert(data);
  })
  .fail(function(jqxhr, textStatus, error) {
		alert('Error: '+jqxhr.responseText);
  });
});

jQuery("#horserace_table").jqGrid({
   	url:'json/horserace.json',
	datatype: "json",
   	colNames:['Id','Name','BearPit', 'Estimate','Notes'],
   	colModel:[
   		{name:'id',index:'id', width:55},
   		{name:'name',index:'name', width:100},
   		{name:'bearpit',index:'estimate',width:55},
   		{name:'estimate',index:'estimate',width:55},
   		{name:'notes',index:'notes', width:100}
   	],
   	rowNum:10,
   	rowList:[10,20,30],
   	pager: '#horserace_pager',
   	sortname: 'id',
    viewrecords: true,
    sortorder: "desc",
    caption:"Score Estimates",
    postData:{tourney: function(){return selTourney.val();}}
});
jQuery("horserace_table").jqGrid('navGrid','#horserace_pager',{edit:false,add:false,del:false});
</script>
