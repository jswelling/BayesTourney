{% extends 'base.tpl' %}

{% from "macros.html" import updown_button_script_preamble with context %}
{% from "macros.html" import updown_button_script with context %}
{% from "macros.html" import updown_button_content with context %}
{% from "macros.html" import jqgrid_boilerplate with context %}

{% block pagescripts %}
<script>
{{ updown_button_script_preamble('entrants') }}
var selEntrantsTourney;
var lastsel_entrants;
$(function() {
  "use strict";
  selEntrantsTourney = $('#sel_entrants_tournament');
  selEntrantsTourney.select().change( function() {
    $('#entrants_table').trigger('reloadGrid');
  });
  function tourneySelFun() { return "tourney="+selEntrantsTourney.val(); };
  $("#entrants_table").jqGrid({
    url:'json/entrants.json',
    editurl:'edit/edit_entrants.json',
    postData: {'tourneyId': function() { return selEntrantsTourney.val() || -1; } },
    colNames:['Id','Name','Notes'],
    colModel:[
      {name:'id',index:'id', width:55, sorttype:'integer'},
      {name:'name',index:'name', width:100, editable:true, edittype:'text'},
      {name:'notes',index:'notes', width:100, editable:true, edittype:'textarea'}
    ],
    onSelectRow: function(id){ 
      if(id && id!==lastsel_entrants){
	$(this).jqGrid('saveRow',lastsel_entrants);
	$(this).jqGrid('editRow',id,true);
	lastsel_entrants=id;
      }
    },
    sortname: 'id',
    caption:"Entrants",
    {{ jqgrid_boilerplate() }}
  });
  $("#add_entrant_button").click( function() {
    $("#entrants_table").jqGrid('editGridRow',"new",{closeAfterAdd:true});
  });
  $("#del_entrant_button").click( function() {
    $("#entrants_table").jqGrid('delGridRow',lastsel_entrants,{});
    lastsel_entrants=null;
  });
  $("#reload_entrant_button").click( function() {
    $("#entrants_table").jqGrid('editRow', lastsel_entrants, false);
    $("#entrants_table").trigger('reloadGrid',{ fromServer: true });
    lastsel_entrants=null;
  });
  {{ updown_button_script('entrants', '/ajax/entrants_download',
			  "tourneySelFun" ) }}

});
</script>
{% endblock %}

{% block content %}
  <h1>Entrants</h1>

  <label for="sel_entrants_tournament">Which Tournament?</label>
  <select id="sel_entrants_tournament">
    <option value="-1">All</option>
    {% for id, name in tourneyDict | dictsort %}
    <option value="{{id}}">{{name}}</option>
    {% endfor %}
  </select>
  <table id="entrants_table"></table>
  <div>
    <input type="BUTTON" id="add_entrant_button" value="New Entrant">
    <input type="BUTTON" id="del_entrant_button" value="Delete Selected Entrant">
    <input type="BUTTON" id="reload_entrant_button" value="Reload">
  </div>

  {{ updown_button_content('entrants', 'Entrants',
       'Upload A Table Of Entrants',
       '/upload/entrants', '/ajax/entrants_download',
       """
       Entrants can be uploaded as a .csv or .tsv file in the same format as
       those downloaded from this page.
       """   
     )
  }}



{% endblock %}
