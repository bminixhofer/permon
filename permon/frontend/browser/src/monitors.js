import echarts from 'echarts';
import clone from 'clone';
import { setStatus } from './status';

const charts = document.querySelector('.charts');
const { fps, buffersize } = charts.dataset;

// treat the client as not connected if no update has been received for 3 seconds
// or for 3 frames if that is more than 3 seconds
const updateTimeout = Math.max(3000, 1000 / fps * 3);

// tracks all chart update functions
const updateFunctions = [];

// stores the latest stat data of every displayed stat
let currentData = {};

// tracks the current mouse position to keep tooltip on the mouse
const mousePos = {
  x: 0,
  y: 0,
};

const categoryResolution = 100;
const adaptiveMinPercentage = 0.8;
const adaptiveMaxPercentage = 1.2;

const defaultContributorAxisOptions = {
  type: 'category',
  boundaryGap: true,
  axisLabel: {
    textStyle: {
      color: 'black',
      fontFamily: 'Roboto Mono',
    },
  },
  axisTick: {
    alignWithLabel: true,
    lineStyle: {
      width: 2,
    },
  },
  splitLine: {
    show: false,
  },
  axisLine: {
    lineStyle: {
      width: 2,
    },
  },
  axisPointer: {
    show: false,
  },
  data: [],
  min: 0,
  max: categoryResolution,
};

function formatLabel(label) {
  const value = Math.abs(label);
  let out = label;
  if (value <= 10) {
    out = Math.round(label * 1000) / 1000;
  } else if (value <= 100) {
    out = Math.round(label * 100) / 100;
  } else if (value <= 1000) {
    out = Math.round(label * 10) / 10;
  } else if (value <= 10000) {
    out = Math.round(label / 50) * 50;
  } else if (value > 10000) {
    out = Math.round(label / 100) * 100;
  }

  return out;
}

const defaultChartOptions = {
  grid: {
    left: 60,
    top: 10,
    right: 60,
    bottom: 10,
  },
  tooltip: {
    trigger: 'axis',
    triggerOn: 'none',
    formatter: tooltip => formatLabel(tooltip[0].value[1]),
    axisPointer: {
      type: 'none',
    },
    position: point => [point[0], '0'],
    textStyle: {
      fontFamily: 'Roboto Mono',
    },
    extraCssText: 'height: calc(100% - 10px); border-radius: 0; border-left: 2px solid #333; background: none; color: #333;',
  },
  xAxis: {
    type: 'value',
    show: false,
    min: value => value.min + 1,
    max: 'dataMax',
  },
  yAxis: [
    {
      type: 'value',
      boundaryGap: [0, '100%'],
      splitLine: {
        show: false,
      },
      axisTick: {
        lineStyle: {
          width: 2,
        },
      },
      axisLine: {
        lineStyle: {
          width: 2,
        },
      },
      axisLabel: {
        formatter: value => formatLabel(value),
        textStyle: {
          color: 'black',
          fontFamily: 'Roboto Mono',
        },
      },
    },
  ],
  series: [{
    symbol: 'none',
    type: 'line',
    showSymbol: false,
    hoverAnimation: false,
    animationEasingUpdate: 'linear',
    animationDurationUpdate: 1000 / fps,
    lineStyle: {
      width: 3,
    },
  }],
};

// stores the date the latest message from the server was received
// to check if the connection has been lost
// this can be set to the current time because there has to be a connection
// to receive the javascript file
let lastUpdateDate = Date.now();

export function setupSocket() {
  const webSocketPrefix = window.location.protocol === 'http:' ? 'ws' : 'wss';
  const socket = new WebSocket(`${webSocketPrefix}://${window.location.host}/stats`);
  socket.onmessage = function onSocketMessage(event) {
    lastUpdateDate = Date.now();
    const eventData = JSON.parse(event.data);
    const currentKeys = Object.keys(currentData);

    const dataKeysChanged = JSON.stringify(Object.keys(eventData)) !== JSON.stringify(currentKeys);
    if (currentKeys.length > 0 && dataKeysChanged) {
      // window.location.reload();
    }
    // store the latest update from the WebSocket in currentData
    currentData = eventData;
  };
}

export function setupMonitor(stat) {
  const {
    tag, maximum, minimum, color, history,
  } = stat;
  const tickPositions = [];
  const labelPositions = [];

  const contributorAxisOptions = clone(defaultContributorAxisOptions);
  contributorAxisOptions.axisLabel.interval = function interval(y) {
    return labelPositions.includes(y);
  };
  contributorAxisOptions.axisTick.interval = function interval(y) {
    return tickPositions.includes(y);
  };

  const chartContainer = document.getElementById(tag);
  const heading = document.createElement('h2');
  heading.textContent = stat.name;

  const chartElement = document.createElement('div');
  chartElement.classList.add('chart');

  // add title and chart to the container div
  // the container div has already been added via the index.html template
  chartContainer.appendChild(heading);
  chartContainer.appendChild(chartElement);

  let dataIndex = 0;
  function makePoint(x) {
    // utiltity function to create a 2d point with steadily increasing x
    dataIndex += 1;
    return {
      name: dataIndex,
      value: [
        dataIndex,
        x,
      ],
    };
  }

  let data = [];
  for (let i = 0; i < buffersize - history.length; i += 1) {
    data.push(makePoint(0));
  }
  data = data.concat(history.map(x => makePoint(x)));

  const chart = echarts.init(chartElement);
  const contributorData = Array(categoryResolution).fill('');

  let axisMin;
  let axisMax;
  if (minimum == null) {
    axisMin = value => adaptiveMinPercentage * value.min;
  } else {
    axisMin = minimum;
  }

  if (maximum == null) {
    axisMax = value => adaptiveMaxPercentage * value.max;
  } else {
    axisMax = maximum;
  }

  const chartOptions = clone(defaultChartOptions);
  chartOptions.yAxis[0].min = axisMin;
  chartOptions.yAxis[0].max = axisMax;
  chartOptions.yAxis.push(contributorAxisOptions);
  chartOptions.color = [color];
  chartOptions.series[0].name = tag;
  chartOptions.series[0].data = data;

  chart.setOption(chartOptions);

  let tooltipRepeater;

  window.addEventListener('resize', () => {
    // disable and reenable animation on resize to prevent awkward lagging of the chart
    chart.setOption({
      animation: false,
    });
    chart.resize();
    chart.setOption({
      animation: true,
    });
  });

  chartElement.addEventListener('mouseover', (event) => {
    // register an interval that updates the tooltip position every 100ms on mouse over a chart
    tooltipRepeater = setInterval(() => {
      const rect = chartElement.getBoundingClientRect();
      chart.dispatchAction({
        type: 'showTip',
        x: (mousePos.x || event.pageX) - rect.x,
        y: (mousePos.y || event.pageY) - rect.y,
      });
    }, 100);
  });
  chartElement.addEventListener('mouseout', () => {
    // clear the interval and hide the tip when the mouse moves out of the chart
    chart.dispatchAction({
      type: 'hideTip',
    });
    clearInterval(tooltipRepeater);
  });

  let value;
  let contributors;
  function updateChart() {
    data.shift();
    // set the chart to 0 if no data is available.
    if (!currentData[tag]) {
      value = 0;
      contributors = null;
    } else if (currentData[tag].constructor === Array) {
      // if the data for the tag is an array, it contains a contributor breakdown
      [value, contributors] = currentData[tag];
    } else {
      // otherwise, only the value is sent
      value = currentData[tag];
      contributors = null;
    }

    data.push(makePoint(value));

    if (contributors) {
      // clear tickPositiions and labelPositions array
      tickPositions.length = 0;
      labelPositions.length = 0;

      let position = 0;
      let labelPosition = 0;
      let contributorSize;
      let contributorMax;
      if (maximum == null) {
        contributorMax = data.reduce((a, b) => Math.max(b.value[1], a), -Infinity);
        contributorMax *= adaptiveMaxPercentage;
      } else {
        contributorMax = maximum;
      }

      contributors.forEach(([key, contributorValue]) => {
        contributorSize = Math.round(contributorValue / contributorMax * categoryResolution);
        // add the contributor size to the start position of the next contributor
        position += contributorSize;
        // subtract half of the contributor size to the label position
        // to make it centered between ticks
        labelPosition = position - Math.floor(contributorSize / 2);

        contributorData[labelPosition] = key;
        tickPositions.push(position);
        labelPositions.push(labelPosition);
      });
      contributorAxisOptions.data = contributorData;
    }
    chart.setOption({
      series: [{
        data,
      }],
      yAxis: [{}, contributorAxisOptions],
    });
  }
  updateFunctions.push(updateChart);
}

export function setupMonitors(stats) {
  window.addEventListener('mousemove', (event) => {
    // we need the mouse position to display tooltips, so keep track of it globally
    mousePos.x = event.pageX;
    mousePos.y = event.pageY;
  });

  // setup a monitor for every stat
  stats.forEach(stat => setupMonitor(stat));
  setInterval(() => {
    // the app is considered connected if it has recently received a message via WebSockets
    const isConnected = Date.now() - lastUpdateDate < updateTimeout;
    setStatus(isConnected);
    if (isConnected) {
      // update function contains a function to update each monitor
      updateFunctions.forEach(func => func());
    }
  }, 1000 / fps);
}
