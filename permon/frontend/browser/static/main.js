let currentData = {};

function setupMonitor(stat) {
    const bufferSize = 50;
    const tag = stat["tag"];
    const maximum = stat["maximum"];
    const minimum = stat["minimum"];
    const color = stat["color"];
    const history = stat["history"];

    let dataIndex = 0;
    function makePoint(x) {
        dataIndex++;
        return {
            name: dataIndex,
            value: [
                dataIndex,
                x
            ]
        }
    }

    let data = [];
    for(let i = 0; i < bufferSize - history.length; i++) {
        data.push(makePoint(0));
    }
    data = data.concat(history.map(x => makePoint(x)));

    let chart = echarts.init(document.getElementById(tag));
    let options = {
        grid: {
            left: "5%",
            top: 10,
            right: "5%",
            bottom: 10
        },
        tooltip: {
            trigger: "axis",
            axisPointer: {
                animation: false
            }
        },
        xAxis: {
            type: "value",
            show: false,
            min: "dataMin",
            max: "dataMax"
        },
        yAxis: [
            {
                type: "value",
                boundaryGap: [0, "100%"],
                splitLine: {
                    show: false
                },
                min: Math.round(minimum) || null,
                max: Math.round(maximum) || null
            },
            // {
            //     type: "category",
            //     boundaryGap: true,
            //     axisLabel: {
            //         interval: function(y) {
            //             return y % 10 == 0;
            //         },
            //         textStyle: {
            //             color: "#000",
            //         }
            //     },
            //     axisTick: {
            //         interval: function(y) {
            //             return y % 20 == 0;
            //         }
            //     },
            //     splitLine: {
            //         show: false
            //     },
            //     data: ["permon", "chromium", "Xorg"],
            //     min: 0,
            //     max: 100,
            // }
        ],
        color: [color],
        series: [{
            name: tag,
            type: "line",
            showSymbol: false,
            hoverAnimation: false,
            data,
            animationEasingUpdate: "linear",
            animationDurationUpdate: 1000
        }]
    };
    chart.setOption(options);

    setInterval(function () {
        data.shift();
        data.push(makePoint(currentData[tag] || 0));

        chart.setOption({
            series: [{
                data
            }]
        });
    }, 1000);
}

let request = new Request(`${window.location.protocol}//${window.location.host}/statInfo`);
fetch(request).then(response => response.json()).then(stats => {
    stats.forEach(stat => {
        setupMonitor(stat);
    });
});

let socket = new WebSocket(`ws://${window.location.host}/statUpdates`);
socket.onmessage = function (event) {
    eventData = JSON.parse(event.data);

    if(Object.keys(currentData).length > 0 && (JSON.stringify(Object.keys(eventData)) !== JSON.stringify(Object.keys(currentData)))) {
        window.location.reload();
    }
    currentData = eventData;
}