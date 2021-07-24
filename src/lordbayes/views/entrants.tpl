{% extends 'base.tpl' %}

{% from "macros.html" import upload_dialog_script with context %}
{% from "macros.html" import upload_dialog_content with context %}

{% block pagescripts %}
<script>
var selEntrantsTourney;
var lastsel_entrants;
var dialog_entrants_upload;
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
	$(this).jqGrid('saveRow',lastsel_entrants);
	$(this).jqGrid('editRow',id,true);
	lastsel_entrants=id;
      }
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
  jQuery("#download_entrants_button").click( function() {
    $("#download_entrants_link")[0].click();
  });
  jQuery("#upload_entrants_button").click( function() {
    dialog_entrants_upload.dialog( "open" );
  });
  selEntrantsTourney.select().change( function() {
    $('#download_entrants_link').attr('href',
				      '/ajax/entrants_download?tourney=' + selEntrantsTourney.val());
    $('#entrants_table').trigger('reloadGrid');
  });

{{ upload_dialog_script('entrants') }}
  
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
    <input type="BUTTON" id="upload_entrants_button" value="Upload Entrants">
  </div>
  <div id="download_entrants_div" class="float-child">
    <button id="download_entrants_button">Download Entrants</button>
    <a id="download_entrants_link" href="/ajax/entrants_download"></a>
  </div>

{{
upload_dialog_content(
  "entrants", "Upload A Table Of Entrants",
  "/upload/entrants",
  """
  Entrants can be uploaded as a .csv or .tsv file in the same format as
  those downloaded from this page.
  """)
}}


{% endblock %}
