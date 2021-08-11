{% extends 'base.tpl' %}

{% from "macros.html" import updown_button_script_preamble with context %}
{% from "macros.html" import updown_button_script with context %}
{% from "macros.html" import updown_button_content with context %}
{% from "macros.html" import jqgrid_boilerplate with context %}

{% block pagescripts %}
<script>
{{ updown_button_script_preamble('bouts') }}
var lastsel_bouts;
var selBoutsTourney;
$(function() {
  "use strict";
  selBoutsTourney = $('#sel_bouts_tournament');
  selBoutsTourney.select().change( function() {
    $('#bouts_table').trigger('reloadGrid');
  });
  function tourneySelFun() { return "tourney="+selBoutsTourney.val(); };
  jQuery("#bouts_table").jqGrid({
    url:'json/bouts.json',
    editurl:'edit/edit_bouts.json',
    postData: {'tourneyId': function() { return selBoutsTourney.val() || -1; } },
    colNames:['Tourney','Wins', 'Player 1','Draws', 'Player 2','Wins','Notes'],
    colModel:[
      {name:'tourney','index':'tourney',width:200, align:'center',
       editable:true, edittype:'select', editoptions:{dataUrl:'list/select_tourney'}},
      {name:'lwins',index:'lwins', width:90, align:'right', 
       editable:true, edittype:'text', editrules: { number:true }},
      {name:'leftplayer',index:'leftplayer', width:100, align:'left',
       editable:true, edittype:'select', editoptions:{dataUrl:'list/select_entrant'}},
      {name:'draws',index:'draws', width:90, align:'left',
       editable:true, edittype:'text', editrules: { number:true }},
      {name:'rightplayer',index:'rightplayer', width:100, align:'right',
       editable:true, edittype:'select', editoptions:{dataUrl:'list/select_entrant'}},
      {name:'rwins',index:'rwins', width:90, align:'left',
       editable:true, edittype:'text', editrules: { number:true }},
      {name:'notes',index:'notes', width:200,
       editable:true, edittype:'textarea'},
    ],
    onSelectRow: function(id){
      if(id && id!==lastsel_bouts){
	$(this).jqGrid('saveRow',lastsel_bouts);
	$(this).jqGrid('editRow',id,true);
	lastsel_bouts=id;
      }
    },
    sortname: 'leftplayer',
    caption:"Bouts",
    {{ jqgrid_boilerplate() }}
  });
  $("#add_bout_button").click( function() {
    jQuery("#bouts_table").jqGrid('editGridRow',"new",{closeAfterAdd:true});
  });
  $("#del_bout_button").click( function() {
    jQuery("#bouts_table").jqGrid('delGridRow',lastsel_bouts,{});
    lastsel_bouts=null;
  });
  $("#reload_bout_button").click( function() {
    $("#bouts_table").trigger('reloadGrid',{ fromServer: true });
    lastsel_entrants=null;
  });
  {{ updown_button_script('bouts', '/ajax/bouts_download',
			  "tourneySelFun" ) }}
});
</script>
{% endblock %}

{% block content %}
<h1>Bouts</h1>

<label for="sel_bouts_tournament">Which Tournament?</label>
<select id="sel_bouts_tournament">
<option value=-1>All</option>
{% for id, name in tourneyDict | dictsort %}
<option value={{id}}>{{name}}</option>
{% endfor %}
</select>
<table id="bouts_table"></table>
<!-- <div id="bouts_pager"></div> -->
<input type="BUTTON" id="add_bout_button" value="New Bout">
<input type="BUTTON" id="del_bout_button" value="Delete Selected Bout">
<input type="BUTTON" id="reload_bout_button" value="Reload">

  {{ updown_button_content('bouts', 'Bouts',
       'Upload A Table Of Bouts',
       '/upload/bouts', '/ajax/bouts_download',
       """
       Bouts can be uploaded as a .csv or .tsv file in the same format as
       those downloaded from this page.
       """,
       'true'
     )
  }}


{% endblock %}
