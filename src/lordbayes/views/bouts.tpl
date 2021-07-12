{% extends 'base.tpl' %}

{% block pagescripts %}
<script>
var lastsel_bouts;
var selBoutsTourney;
$(function() {
  "use strict";
  selBoutsTourney = $('#sel_bouts_tournament');
  jQuery("#bouts_table").jqGrid({
    url:'json/bouts.json',
    postData: {'tourneyId': function() { return selBoutsTourney.val() || -1; } },
    datatype: "json",
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
	jQuery('#bouts_table').jqGrid('saveRow',lastsel_bouts);
	jQuery('#bouts_table').jqGrid('editRow',id,true);
	lastsel_bouts=id;
      }
    },
    beforeProcessing: function(data, status, xhr) {
      console.log(data, status, xhr);
    },
    rowNum:5,
    rowList:[5,10,20,30],
    pager: true,
    cmTemplate: { autoResizable: true },
    autoresizeOnLoad: true,
    loadonce: true,
    reloadGridOptions: { fromServer: true, reloadAfterSubmit: true },
    sortname: 'leftplayer',
    sortorder: "desc",
    caption:"Bouts",
    editurl:'edit/edit_bouts.json',
    guiStyle: "bootstrap",
    iconSet: "fontAwesome"  
  });
  jQuery("#add_bout_button").click( function() {
    jQuery("#bouts_table").jqGrid('editGridRow',"new",{closeAfterAdd:true});
  });
  jQuery("#del_bout_button").click( function() {
    jQuery("#bouts_table").jqGrid('delGridRow',lastsel_bouts,{});
    lastsel_bouts=null;
  });
  jQuery("#reload_bout_button").click( function() {
    $("#bouts_table").trigger('reloadGrid',{ fromServer: true });
    lastsel_entrants=null;
  });
  selBoutsTourney.select().change( function() {
    $('#download_bouts_link').attr('href', '/ajax/bouts_download?tourney=' + selBoutsTourney.val());
    $('#bouts_table').trigger('reloadGrid');
  });
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
<a id="download_bouts_link" href="/ajax/bouts_download?tourney=-1">Download these bouts as .tsv</a>

{% endblock %}
