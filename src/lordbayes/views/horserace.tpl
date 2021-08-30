{% extends 'base.tpl' %}

{% from "macros.html" import sel_tournaments with context %}

{% block pagescripts %}

<script>
  
var selTourney;
var goBtn;
function include_cb_change() {
  var trimmed_id = this.id.slice(this.id.lastIndexOf("_")+1);
  var data = {
    "tourney_id": $("#sel_horserace_tournament").val(),
    "player_id": trimmed_id,
    "state": this.checked
  };
  $.ajax({type:'PUT',
	  url:'ajax/horserace/checkbox',
	  data:data,
	  //contentType: "application/json; charset=utf-8",
	  dataType: "json"
	 })
    .done(function(data, textStatus, jqXHR) {
      if (data['status'] != "success") {
	if (data['msg'] == undefined) {
	  alert('The server failed to save this update');
	}
	else {
	  alert('The server failed to save this update: ' + data['msg']);
	}
	window.location.reload();
      }
    })
    .fail(function(jqXHR, textStatus, errorThrown) {
      alert('An error occurred: ' + errorThrown);
      window.location.reload();
    })
}
$(function() {
  selTourney = $('#sel_horserace_tournament');
  goBtn = $('#horserace_go_btn');
  selTourney.select().change( function()
			      {
				$('#horserace_table').trigger('reloadGrid');
			      });
  goBtn.button().click( function()
			{
			  checkboxData = {};
			  $('#horserace_table').jqGrid('getRowData')
			    .forEach(element => {
			      var thisId = element.id;
			      checkboxData[thisId] = $('#horserace_checkbox_' + thisId)[0].checked;
			    });
			  jsonData = {
			    tourney: selTourney.val(),
			    checkboxes: checkboxData
			  };
			  console.log(jsonData);
			  $.ajax({type:'POST',
				  url:'horserace_go',
				  data:JSON.stringify(jsonData),
				  contentType: "application/json; charset=utf-8",
				  dataType: "json"
				 })
			    .done( function(data) {
			      $('#announcement_div').html(data['announce_html']);
			      $('#horseraceImage').html(data['image']);
			    })
			    .fail(function(jqxhr, textStatus, error) {
			      alert('Error: '+jqxhr.responseText);
			    });
			});
})
$(function() {
  "use strict";
  jQuery("#horserace_table").jqGrid({
    url:'json/horserace',
    postData:{tourney: function(){return selTourney.val() || -1;}},
    datatype: "json",
    colNames:['Id','Name','Wins', 'Losses', 'Draws',
	      'BearPit', 'Include'],
    colModel:[
      {name:'id',index:'id', width:55},
      {name:'name',index:'name', width:100},
      {name:'wins',index:'wins',width:55},
      {name:'losses',index:'losses',width:55},
      {name:'draws',index:'draws',width:55},
      {name:'bearpit',index:'bearpit',width:55},
      {sortable:false, name:'include', index:'id', width:100,
       formatter: function(cellvalue, options, rowobject){
	 var word_checked;
	 var idx = cellvalue.slice(0,-1);
	 if (cellvalue.slice(-1) == '+') {word_checked = ' checked '}
	 else {word_checked = ' '};
	 return '<input type="checkbox" class="includecb" id="horserace_checkbox_'+ idx + '"' + word_checked + '>';
       }
      }
    ],
    rowNum:10,
    rowList:[10,20,30],
    pager: true,
    cmTemplate: { autoResizable: true },
    autoresizeOnLoad: true,
    loadonce: true,
    reloadGridOptions: { fromServer: true, reloadAfterSubmid: true },
    sortname: 'id',
    sortorder: "desc",
    viewrecords: true,
    caption:"Score Estimates",
    guiStyle: "bootstrap",
    iconSet: "fontAwesome",
    gridComplete: function() {
      $("#horserace_table").find('input:checkbox.includecb').change(include_cb_change);
    }
  })    
  jQuery("#reload_horserace_button").click( function() {
    $("#horserace_table").trigger('reloadGrid',{ fromServer: true });
    lastsel_entrants=null;
  });
});
</script>
{% endblock %}

{% block content %}
<h1>Horserace</h1>

{{ sel_tournaments('sel_horserace_tournament') }}

<div>
  <table id="horserace_table"></table>
  <button id="horserace_go_btn">Go!</button>
  <input type="BUTTON" id="reload_horserace_button" value="Reload">
</div>
  <div id='announcement_div'>
  <p>
  Click 'go' to analyze the selected tournament.
  </p>
  </div>
  <div id="horseraceImage">
  </div>

{% endblock %}
