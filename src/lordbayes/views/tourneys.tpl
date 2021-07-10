{% extends 'base.tpl' %}

{% block pagescripts %}
<script>
var lastsel_tourneys;
$(function () {
  "use strict";
  jQuery("#tourneys_table").jqGrid({
    url:'json/tourneys.json',
    datatype: "json",
    colNames:['Id','Name','Notes'],
    colModel:[
      {name:'id',index:'id', width:55, sortable:true, sorttype:'integer'},
      {name:'name',index:'name', width:100, editable:true, edittype:'text', sortable:true},
      {name:'notes',index:'notes', width:100, editable:true, edittype:'textarea', sortable:true}
    ],
    onSelectRow: function(id){
      if(id && id!==lastsel_tourneys){
	jQuery('#tourneys_table').jqGrid('saveRow',lastsel_tourneys);
	jQuery('#tourneys_table').jqGrid('editRow',id,true);
	lastsel_tourneys=id;
      }
    },
    rowNum:10,
    rowList:[10,20,30],
    sortname: 'id',
    sortorder: "desc",
    caption:"Tourneys",
    editurl:'edit/edit_tourneys.json',
    //toppager: true,
    pager: true,
    guiStyle: "bootstrap",
    iconSet: "fontAwesome",
    cmTemplate: { autoResizable: true },
    autoresizeOnLoad: true,
    loadonce: true,
    reloadGridOptions: { fromServer: true, reloadAfterSubmit: true },    
  });
  jQuery("#add_tourney_button").click( function() {
    $("#tourneys_table").jqGrid('editGridRow', "new",
				{closeAfterAdd: true, reloadAfterSubmit: true});
  });
  jQuery("#del_tourney_button").click( function() {
    jQuery("#tourneys_table").jqGrid('delGridRow',lastsel_tourneys,{});
    lastsel_tourneys=null;
  });
  jQuery("#reload_tourney_button").click( function() {
    $("#tourneys_table").trigger('reloadGrid',{ fromServer: true });
    lastsel_tourneys=null;
  });

});
</script>
{% endblock %}

{% block content %}
<h1>Known Tournaments</h1>

<table id="tourneys_table"></table>

<input type="BUTTON" id="add_tourney_button" value="New Tourney">
<input type="BUTTON" id="del_tourney_button" value="Delete Selected Tourney">
<input type="BUTTON" id="reload_tourney_button" value="Reload">
{% endblock %}

