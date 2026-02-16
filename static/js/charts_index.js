import { plot_ts, plot_pie } from "./utils.js";

function plot_ts_sales(){

    plot_ts({
        div_id: '#ts-sales',
        x: ts_sales["date"],
        y: ts_sales["total_sales"]
    });
    
}

function plot_pie_sales(){
    
    // Top countries by perc of sales
    plot_pie({
        div_id: '#pie-countries',
        values: sales_countries["total_sales"],
        labels: sales_countries["country"]
    });

    // Items by perc of sales
    plot_pie({
        div_id: '#pie-items',
        values: sales_items["total_sales"],
        labels: sales_items["name"]
    });
}

document.addEventListener('DOMContentLoaded', plot_ts_sales)
document.addEventListener('DOMContentLoaded', plot_pie_sales)