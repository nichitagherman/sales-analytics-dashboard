console.log(customers)

//custom max min header filter
var minMaxFilterEditor = function(cell, onRendered, success, cancel, editorParams){

    var end;

    var container = document.createElement("span");

    //create and style inputs
    var start = document.createElement("input");
    start.setAttribute("type", "number");
    start.setAttribute("placeholder", "Min");
    start.setAttribute("min", 0);
    start.setAttribute("max", 100);
    start.style.padding = "4px";
    start.style.width = "50%";
    start.style.boxSizing = "border-box";

    start.value = cell.getValue();

    function buildValues(){
        success({
            start:start.value,
            end:end.value,
        });
    }

    function keypress(e){
        if(e.keyCode == 13){
            buildValues();
        }

        if(e.keyCode == 27){
            cancel();
        }
    }

    end = start.cloneNode();
    end.setAttribute("placeholder", "Max");

    start.addEventListener("change", buildValues);
    start.addEventListener("blur", buildValues);
    start.addEventListener("keydown", keypress);

    end.addEventListener("change", buildValues);
    end.addEventListener("blur", buildValues);
    end.addEventListener("keydown", keypress);


    container.appendChild(start);
    container.appendChild(end);

    return container;
 }

//custom max min filter function. source: tabulator.info documentation page
function minMaxFilterFunction(headerValue, rowValue, rowData, filterParams){
    //headerValue - the value of the header filter element
    //rowValue - the value of the column in this row
    //rowData - the data for the row being filtered
    //filterParams - params object passed to the headerFilterFuncParams property

        if(rowValue){
            if(headerValue.start != ""){
                if(headerValue.end != ""){
                    return rowValue >= headerValue.start && rowValue <= headerValue.end;
                }else{
                    return rowValue >= headerValue.start;
                }
            }else{
                if(headerValue.end != ""){
                    return rowValue <= headerValue.end;
                }
            }
        }

    return true; //must return a boolean, true if it passes the filter.
}

var table = new Tabulator("#customers-table", {
    data:customers,

    layout:"fitColumns",
    pagination:"local",
    paginationSize:10,
    paginationSizeSelector:[3, 5, 10, 20],
    movableColumns:true,
    paginationCounter:"rows",
    columns:[
    {title:"ID", field:"id", sorter:"number", headerFilter:"input"},
    {title:"NAME", field:"name", sorter:"text", headerFilter:"input"},
    {title:"PHONE", field:"phone", sorter:"number", headerFilter:"input"},
    {title:"ADDRESS", field:"address", sorter:"text", headerFilter:"input"},
    {title:"CITY", field:"city", sorter:"text", headerFilter:"input"},
    {title:"COUNTRY", field:"country", sorter:"text", headerFilter:"input"},
    {title:"TOTAL SALES", field:"total_sales", sorter:"number", headerFilter:minMaxFilterEditor, headerFilterFunc:minMaxFilterFunction, headerFilterLiveFilter:false, formatter:"money", formatterParams:{
        decimal:".",
        thousand:",",
        symbol:"$",
        negativeSign:true,
        precision:0,
    }},
    ],
    initialSort:[
        {columns:"TOTAL SALES", dir:"desc"}
    ]
});

document.getElementById("download-csv").addEventListener("click", function(){
    table.downloadToTab("csv");
});
