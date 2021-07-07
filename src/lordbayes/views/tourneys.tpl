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
      {name:'id',index:'id', width:55},
      {name:'name',index:'name', width:100, editable:true, edittype:'text'},
      {name:'notes',index:'notes', width:100, editable:true, edittype:'textarea'}
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
    viewrecords: true,
    sortorder: "desc",
    caption:"Tourneys",
    editurl:'edit/edit_tourneys.json',
    //toppager: true,
    pager: true,
    guiStyle: "bootstrap",
    iconSet: "fontAwesome"
    //edit: true,
    //editTitle: "Edit this", width:500,
    // edit : {
    //   addCaption: "Add Record",
    //   editCaption: "Edit Record",
    //   bSubmit: "Submit",
    //   bCancel: "Cancel",
    //   bClose: "Close",
    //   saveData: "Data has been changed! Save changes?",
    //   bYes : "Yes",
    //   bNo : "No",
    //   bExit : "Cancel",
    // }    	
  })
});
  //jQuery("tourneys_table").jqGrid('navGrid','#tourneys_pager',{edit:false,add:false,del:false});
jQuery("#add_tourney_button").click( function() {
	jQuery("#tourneys_table").jqGrid('editGridRow',"new",{closeAfterAdd:true});
});
</script>
{% endblock %}

{% block content %}
<h1>Known Tournaments</h1>

<table id="tourneys_table"></table>

<input type="BUTTON" id="add_tourney_button" value="New Tourney">
{% endblock %}

