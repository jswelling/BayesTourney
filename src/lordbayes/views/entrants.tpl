{% extends 'base.tpl' %}

{% block pagescripts %}
<script>
var selEntrantsTourney;
var lastsel_entrants;
$(function() {
  "use strict";
  selEntrantsTourney = $('#sel_entrants_tournament');
  jQuery("#entrants_table").jqGrid({
    url:'json/entrants.json',
    postData: {'tourneyId': function() { return selEntrantsTourney.val() || -1; } },
    datatype: "json",
    colNames:['Id','Name','Notes'],
    colModel:[
      {name:'id',index:'id', width:55, sorttype:'integer'},
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
    beforeProcessing: function(data, status, xhr) {
      console.log(data, status, xhr);
    },
    rowNum:5,
    rowList:[5,10,20,30],
    pager: '#entrants_pager',
    sortname: 'id',
    sortorder: "desc",
    caption:"Entrants",
    pager: true,
    guiStyle: "bootstrap",
    iconSet: "fontAwesome",
    editurl:'edit/edit_entrants.json',
    cmTemplate: { autoResizable: true },
    autoresizeOnLoad: true,
    loadonce: true,
    reloadGridOptions: { fromServer: true, reloadAfterSubmit: true },    
  });
  jQuery("#add_entrant_button").click( function() {
    jQuery("#entrants_table").jqGrid('editGridRow',"new",{closeAfterAdd:true});
  });
  jQuery("#del_entrant_button").click( function() {
    jQuery("#entrants_table").jqGrid('delGridRow',lastsel_entrants,{});
    lastsel_entrants=null;
  });
  jQuery("#reload_entrant_button").click( function() {
    $("#entrants_table").trigger('reloadGrid',{ fromServer: true });
    lastsel_entrants=null;
  });
  selEntrantsTourney.select().change( function() {
    $('#download_entrants_link').attr('href',
				      '/ajax/entrants_download?tourney=' + selEntrantsTourney.val());
    $('#entrants_table').trigger('reloadGrid');
  });
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
<input type="BUTTON" id="add_entrant_button" value="New Entrant">
<input type="BUTTON" id="del_entrant_button" value="Delete Selected Entrant">
<input type="BUTTON" id="reload_entrant_button" value="Reload">
<a id="download_entrants_link" href="/ajax/entrants_download?tourney=-1">Download these entrants as .tsv</a>

{% endblock %}
