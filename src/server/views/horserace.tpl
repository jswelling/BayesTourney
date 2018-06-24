<h1>Horserace</h1>

<table id="horserace_table"></table>
<div id="horserace_pager"></div>

<script>
var lastsel_horserace;
jQuery("#horserace_table").jqGrid({
   	url:'json/horserace.json',
	datatype: "json",
   	colNames:['Id','Name','Estimate','Notes'],
   	colModel:[
   		{name:'id',index:'id', width:55},
   		{name:'name',index:'name', width:100},
   		{name:'estimate',index:'estimate',width:55},
   		{name:'notes',index:'notes', width:100}
   	],
   	rowNum:10,
   	rowList:[10,20,30],
   	pager: '#horserace_pager',
   	sortname: 'id',
    viewrecords: true,
    sortorder: "desc",
    caption:"Score Estimates",
});
jQuery("horserace_table").jqGrid('navGrid','#horserace_pager',{edit:false,add:false,del:false});
</script>
