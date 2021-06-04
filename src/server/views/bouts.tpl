<h1>Bouts</h1>

<label for="sel_bouts_tournament">Which Tournament?</label>
<select id="sel_bouts_tournament">
<option value=-1>All</option>
{% for id, name in tourneyDict | dictsort %}
<option value={{id}}>{{name}}</option>
{% endfor %}
</select>
<table id="bouts_table"></table>
<div id="bouts_pager"></div>
<input type="BUTTON" id="add_bout_button" value="New Bout">
<input type="BUTTON" id="del_bout_button" value="Delete Selected Bout">
<a id="download_bouts_link" href="/ajax/bouts_download?tourney=-1">Download these bouts as .tsv</a>

<script>
var selBoutsTourney = $('#sel_bouts_tournament');
selBoutsTourney.select().change( function()
{
  $('#download_bouts_link').attr('href', '/ajax/bouts_download?tourney=' + selBoutsTourney.val());
  $('#bouts_table').trigger('reloadGrid');
});

var lastsel_bouts
jQuery("#bouts_table").jqGrid({
  url:'json/bouts.json',
  postData: {'tourneyId': function() { return selBoutsTourney.val(); } },
  datatype: "json",
  colNames:['Tourney','Wins', 'Player 1','Draws', 'Player 2','Wins','Notes'],
  colModel:[
    {name:'tourney','index':'tourney',width:100, align:'center',
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
    {name:'notes',index:'notes', width:100,
     editable:true, edittype:'textarea'},
  ],
  onSelectRow: function(id){
    if(id && id!==lastsel_bouts){
      jQuery('#bouts_table').jqGrid('saveRow',lastsel_bouts);
      jQuery('#bouts_table').jqGrid('editRow',id,true);
      lastsel_bouts=id;
    }
  },
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
  },
  rowNum:10,
  rowList:[10,20,30],
  pager: '#bouts_pager',
  sortname: 'leftplayer',
  viewrecords: true,
  sortorder: "desc",
  caption:"Bouts",
  editurl:'edit/edit_bouts.json'
});
jQuery("bouts_table").jqGrid('navGrid','#bouts_pager',{edit:false,add:false,del:false});
jQuery("#add_bout_button").click( function() {
	jQuery("#bouts_table").jqGrid('editGridRow',"new",{closeAfterAdd:true});
});
jQuery("#del_bout_button").click( function() {
	jQuery("#bouts_table").jqGrid('delGridRow',lastsel_bouts,{});
	lastsel_bouts=null;
});
</script>
