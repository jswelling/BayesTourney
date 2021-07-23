{% extends 'base.tpl' %}

{% block pagescripts %}
<script>
var selEntrantsTourney;
var lastsel_entrants;
var dialog;
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
    dialog.dialog( "open" );
  });
  selEntrantsTourney.select().change( function() {
    $('#download_entrants_link').attr('href',
				      '/ajax/entrants_download?tourney=' + selEntrantsTourney.val());
    $('#entrants_table').trigger('reloadGrid');
  });


  dialog = $( "#upload_entrants_dialog" ).dialog({
    autoOpen: false,
    height: 400,
    width: 350,
    modal: true,
    open: function() {
      $("#dlg_msg_span").hide();
    },
    buttons: [
      {
        text: "Upload",
	click: function() {
	  console.log($("#upload_entrants_file").val());
	  if ( $("#upload_entrants_file").val() ) {
	    $("#upload_entrants_form").submit();
	  } else {
	    $("#dlg_msg_span").text("No file selected.").show();
	  }
	},
	type: "submit",
	form: "upload_entrants_form"
	},
      {
	text: "Cancel",
	click: function() {
          dialog.dialog( "close" );
	  }
      	}
    ]
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
  <div>
    <input type="BUTTON" id="add_entrant_button" value="New Entrant">
    <input type="BUTTON" id="del_entrant_button" value="Delete Selected Entrant">
    <input type="BUTTON" id="reload_entrant_button" value="Reload">
    <input type="BUTTON" id="upload_entrants_button" value="Upload Entrants">
  </div>
  <div id="download_entrants_div" class="float-child">
    <button id="download_entrants_button">Download Entrants</button>
    <a id="download_entrants_link"></a>
  </div>

  <div id="upload_entrants_dialog" title="Upload Entrants As Spreadsheet">
    <h1>Upload A Table Of Entrants</h1>
    <form id="upload_entrants_form"
          method=post
	  action="/upload/entrants"
          enctype=multipart/form-data>
      <input type=file name=file id="upload_entrants_file">
      <!--<input type=submit value=Upload> -->
    </form>
    Entrants can be uploaded as a .csv or .tsv file in the same format as
    can be downloaded from this page.
    <br>
    <span id="dlg_msg_span" class="alert alert-warning" role="alert"></span>
  </div>

{% endblock %}
