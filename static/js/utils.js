export function plot_ts({div_id, x, y}){
    let d_ts_sales = document.querySelector(div_id);
    if (!d_ts_sales){
        return;
    }

    let trace_sales = {
        x: x,
        y: y,
        type: "scatter",
        mode: "lines",
        name: "value",
        line: {
            width: 3 
        }
    };

    let layout = {
        autosize: true,
        margin: {
            l: 50,
            r: 50,
            b: 20,
            t: 20,
            pad: 4
        },
        xaxis: {
            autorange: true,
            rangeselector: {buttons: [
                {
                count: 7,
                label: '1W',
                step: 'day',
                stepmode: 'backward'
                },
                {
                count: 1,
                label: '1M',
                step: 'month',
                stepmode: 'backward'
                },
                {
                count: 3,
                label: '3M',
                step: 'month',
                stepmode: 'backward'
                },
                {
                count: 1,
                label: "YTD",
                step: "year",
                stepmode: "todate"
                },
                {
                count: 1,
                label: '1Y',
                step: 'year',
                stepmode: 'backward'
                },
                {step: 'all'}
            ]},
            rangeslider: 'all',
            type: 'date'
        },

    };
    
    return Plotly.newPlot(d_ts_sales, [trace_sales], layout, {displayModeBar: false});
}

export function plot_pie({div_id, values, labels}){
    let d_countries = document.querySelector(div_id);
    if (!d_countries){
        return;
    }
    
    let data = [{
        type: "pie",
        values: values,
        labels: labels,
        textinfo: "label+percent",
        textposition: "outside",
        automargin: true,
        sort: false,
        direction: 'clockwise'
    }];

    let layout = {
        autosize: true,
        margin: {
            l: 50,
            r: 50,
            b: 20,
            t: 20,
            pad: 4
        },
        showlegend: false
    };

    return Plotly.newPlot(d_countries, data, layout, {displayModeBar: false});
}
