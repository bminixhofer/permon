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

// stores the latest stat data of every displayed tag
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
const formatter = value => Math.round(value * 100) / 100;
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
    formatter: tooltip => formatter(tooltip[0].value[1]),
    axisPointer: {
      type: 'none',
    },
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
        formatter: value => formatter(value),
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
  const socket = new WebSocket(`ws://${window.location.host}/stats`);
  socket.onmessage = function onSocketMessage(event) {
    lastUpdateDate = Date.now();
    const eventData = JSON.parse(event.data);
    const currentKeys = Object.keys(currentData);

    const dataKeysChanged = JSON.stringify(Object.keys(eventData)) !== JSON.stringify(currentKeys);
    if (currentKeys.length > 0 && dataKeysChanged) {
      // window.location.reload();
    }
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

  chartContainer.appendChild(heading);
  chartContainer.appendChild(chartElement);

  let dataIndex = 0;
  function makePoint(x) {
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
  const rect = chartElement.getBoundingClientRect();

  window.addEventListener('resize', () => {
    chart.setOption({
      animation: false,
    });
    chart.resize();
    chart.setOption({
      animation: true,
    });
  });

  chartElement.addEventListener('mouseover', (event) => {
    tooltipRepeater = setInterval(() => {
      chart.dispatchAction({
        type: 'showTip',
        x: (mousePos.x || event.pageX) - rect.x,
        y: (mousePos.y || event.pageY) - rect.y,
      });
    }, 100);
  });
  chartElement.addEventListener('mouseout', () => {
    chart.dispatchAction({
      type: 'hideTip',
    });
    clearInterval(tooltipRepeater);
  });

  let value;
  let contributors;
  function updateChart() {
    data.shift();
    if (!currentData[tag]) {
      value = 0;
      contributors = null;
    } else if (currentData[tag].constructor === Array) {
      [value, contributors] = currentData[tag];
    } else {
      value = currentData[tag];
      contributors = null;
    }

    data.push(makePoint(value));

    if (contributors) {
      tickPositions.length = 0;
      labelPositions.length = 0;
      let position = 0;
      let labelPosition = 0;
      let update;
      let contributorMax;
      if (maximum == null) {
        contributorMax = data.reduce((a, b) => Math.max(b.value[1], a), -Infinity);
        contributorMax *= adaptiveMaxPercentage;
      } else {
        contributorMax = maximum;
      }

      contributors.forEach(([key, contributorValue]) => {
        update = Math.round(contributorValue / contributorMax * categoryResolution);
        position += update;
        labelPosition = position - Math.floor(update / 2);

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
    mousePos.x = event.pageX;
    mousePos.y = event.pageY;
  });

  stats.forEach(stat => setupMonitor(stat));
  setInterval(() => {
    const isConnected = Date.now() - lastUpdateDate < updateTimeout;
    setStatus(isConnected);
    if (isConnected) {
      updateFunctions.forEach(func => func());
    }
  }, 1000 / fps);
}
