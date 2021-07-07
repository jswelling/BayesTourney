{% extends 'base.tpl' %}

{% block pagescripts %}
<script>
var selEntrantsTourney = $('#sel_entrants_tournament');
selEntrantsTourney.select().change( function()
{
  $('#download_entrants_link').attr('href', '/ajax/entrants_download?tourney=' + selEntrantsTourney.val());
  $('#entrants_table').trigger('reloadGrid');
});
var lastsel_entrants;
$(function() {
  "use strict";
  jQuery("#entrants_table").jqGrid({
    url:'json/entrants.json',
    postData: {'tourneyId': function() { return selEntrantsTourney.val() || -1; } },
    datatype: "json",
    colNames:['Id','Name','Notes'],
    colModel:[
      {name:'id',index:'id', width:55},
      {name:'name',index:'name', width:100, editable:true, edittype:'text'},
      {name:'notes',index:'notes', width:100, editable:true, edittype:'textarea'}
    ],
    onSelectRow: function(id){
      if(id && id!==lastsel_entrants){
	jQuery('#entrants_table').jqGrid('saveRow',lastsel_entrants);
	jQuery('#entrants_table').jqGrid('editRow',id,true);
	lastsel_entrants=id;
      }
    },
    rowNum:10,
    rowList:[10,20,30],
    pager: '#entrants_pager',
    sortname: 'id',
    viewrecords: true,
    sortorder: "desc",
    caption:"Entrants",
    pager: true,
    guiStyle: "bootstrap",
    iconSet: "fontAwesome",
    editurl:'edit/edit_entrants.json',
    edit : {
      addCaption: "Add Record",
      editCaption: "Edit Record",
      bSubmit: "Submit",
      bCancel: "Cancel",
      bClose: "Close",
      saveData: "Data has been changed! Save changes?",
      bYes : "Yes",
      bNo : "No",
      bExit : "Cancel",
    }
  });
});
  //jQuery("entrants_table").jqGrid('navGrid','#entrants_pager',{edit:false,add:false,del:false});
jQuery("#add_entrant_button").click( function() {
	jQuery("#entrants_table").jqGrid('editGridRow',"new",{closeAfterAdd:true});
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
<div id="entrants_pager"></div>
<input type="BUTTON" id="add_entrant_button" value="New Entrant">
<a id="download_entrants_link" href="/ajax/entrants_download?tourney=-1">Download these entrants as .tsv</a>

{% endblock %}
