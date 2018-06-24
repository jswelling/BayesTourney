<h1>Entrants</h1>

<table id="entrants_table"></table>
<div id="entrants_pager"></div>
<input type="BUTTON" id="add_entrant_button" value="New Entrant">

<script>
var lastsel_entrants;
jQuery("#entrants_table").jqGrid({
   	url:'json/entrants.json',
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
jQuery("entrants_table").jqGrid('navGrid','#entrants_pager',{edit:false,add:false,del:false});
jQuery("#add_entrant_button").click( function() {
	jQuery("#entrants_table").jqGrid('editGridRow',"new",{closeAfterAdd:true});
});
</script>
