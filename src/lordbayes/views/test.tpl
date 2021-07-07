{% extends 'base.tpl' %}

{% block pagescripts %}
    <script>
    //<![CDATA[
    $(function () {
        "use strict";
        $("#grid").jqGrid({
          colModel: [
            { name: "firstName" },
            { name: "lastName" }
          ],
          data: [
            { id: 10, firstName: "Angela", lastName: "Merkel" },
            { id: 20, firstName: "Vladimir", lastName: "Putin" },
            { id: 30, firstName: "David", lastName: "Cameron" },
            { id: 40, firstName: "Barack", lastName: "Obama" },
            { id: 50, firstName: "François", lastName: "Hollande" }
          ],
	  toppager:true,
	  guiStyle: "bootstrap",
	  iconSet: "fontAwesome"
	});
    });
    //]]>
    </script>
{% endblock %}

{% block content %}
<h1>Test</h1>

<table id="grid"></table>
{% endblock %}
