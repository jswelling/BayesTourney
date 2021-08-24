{% extends 'base.tpl' %}

{% block pagescripts %}

<script>
  
var selTourney;
var goBtn;
$(function() {
  selTourney = $('#sel_horserace_tournament');
  goBtn = $('#horserace_go_btn');
  console.log(selTourney);
  console.log(goBtn);
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
    function horserace_checkbox_change(chkbox) { alert(chkbox.checked); }
})
$(function() {
  "use strict";
  jQuery("#horserace_table").jqGrid({
    url:'json/horserace.json',
    postData:{tourney: function(){return selTourney.val() || -1;}},
    datatype: "json",
    colNames:['Id','Name','BearPit', 'Estimate','Notes', 'Include'],
    colModel:[
      {name:'id',index:'id', width:55},
      {name:'name',index:'name', width:100},
      {name:'bearpit',index:'estimate',width:55},
      {name:'estimate',index:'estimate',width:55},
      {name:'notes',index:'notes', width:100},
      {sortable:false, name:'exclude', index:'id', width:100,
       formatter: function(cellvalue, options, rowobject){
	 return '<input type="checkbox" id="horserace_checkbox_'+cellvalue+'" checked>';
       }
      }
    ],
    rowNum:5,
    rowList:[5,10,20,30],
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
    iconSet: "fontAwesome"
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

<label for="sel_horserace_tournament">Which Tournament?</label>
<select id="sel_horserace_tournament">
  <option value=-1>All</option>
  {% for id, name in tourneyDict | dictsort %}
  <option value={{id}}>{{name}}</option>
  {% endfor %}
</select>

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
