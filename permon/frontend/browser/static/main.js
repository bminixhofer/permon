let currentData = {};

socket = new WebSocket(`ws://${window.location.host}/statUpdates`)
socket.onmessage = function (event) {
    currentData = JSON.parse(event.data);
}

let request = new Request(`http://${window.location.host}/statInfo`);
fetch(request).then(response => response.json()).then(stats => {
    stats.forEach(stat => {
        setupMonitor(stat);
    });
});

function setupMonitor(stat) {
    const bufferSize = 50;
    const tag = stat['tag'];
    const maximum = stat['maximum'];
    const minimum = stat['minimum'];
    const color = stat['color'];

    let data_index = 0;
    function makePoint(x) {
        data_index++;
        return {
            name: data_index,
            value: [
                data_index,
                x
            ]
        }
    }

    let data = [];
    for(let i = 0; i < bufferSize; i++) {
        data.push(makePoint(0));
    }

    let chart = echarts.init(document.getElementById(tag));
    let options = {
        grid: {
            left: '5%',
            top: 10,
            right: '5%',
            bottom: 10
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                animation: false
            }
        },
        xAxis: {
            type: 'value',
            show: false,
            min: 'dataMin',
            max: 'dataMax'
        },
        yAxis: [
            {
                type: 'value',
                boundaryGap: [0, '100%'],
                splitLine: {
                    show: false
                },
                min: Math.round(minimum) || null,
                max: Math.round(maximum) || null
            },
            // {
            //     type: 'category',
            //     boundaryGap: true,
            //     axisLabel: {
            //         interval: function(y) {
            //             return y % 10 == 0;
            //         },
            //         textStyle: {
            //             color: '#000',
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
            //     data: ['permon', 'chromium', 'Xorg'],
            //     min: 0,
            //     max: 100,
            // }
        ],
        color: [color],
        series: [{
            name: 'cpu usage',
            type: 'line',
            showSymbol: false,
            hoverAnimation: false,
            data: data,
            animationEasingUpdate: 'linear',
            animationDurationUpdate: 1000
        }]
    };
    chart.setOption(options);

    setInterval(function () {
        data.shift();
        data.push(makePoint(currentData[tag] || 0));

        chart.setOption({
            series: [{
                data: data
            }]
        });
    }, 1000);
}

/*
let data_index = 0;

function randomData() {
    now = new Date(+now + oneDay);
    value = value + Math.random() * 21 - 10;
    return {
        name: data_index,
        value: [
            data_index++,
            Math.round(value)
        ]
    }
}

var data = [];
var now = +new Date(1997, 9, 3);
var oneDay = 3 * 24 * 3600 * 1000;
var value = Math.random() * 1000;
for (var i = 0; i < 50; i++) {
    data.push(randomData());
}

var myChart = echarts.init(document.getElementById('core.cpu_usage'));

// specify chart configuration item and data
option = {
    title: {
        text: '动态数据 + 时间坐标轴'
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            animation: false
        }
    },
    xAxis: {
        type: 'value',
        show: false,
        min: 'dataMin',
        max: 'dataMax'
    },
    yAxis: [
        {
            type: 'value',
            boundaryGap: [0, '100%'],
            splitLine: {
                show: false
            }
        },
        // {
        //     type: 'category',
        //     boundaryGap: true,
        //     axisLabel: {
        //         interval: function(y) {
        //             return y % 10 == 0;
        //         },
        //         textStyle: {
        //             color: '#000',
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
        //     data: ['permon', 'chromium', 'Xorg'],
        //     min: 0,
        //     max: 100,
        // }
    ],
    series: [{
        name: 'cpu usage',
        type: 'line',
        showSymbol: false,
        hoverAnimation: false,
        data: data
    }]
};

// use configuration item and data specified to show chart
myChart.setOption(option);

setInterval(function () {

    for (var i = 0; i < 5; i++) {
        data.shift();
        data.push(randomData());
    }

    myChart.setOption({
        series: [{
            data: data
        }]
    });
}, 1000);*/