/* global echarts */

const charts = document.querySelector('.charts');
const { fps, buffersize } = charts.dataset;
// treat the client as not connected if no update has been received for 3 seconds
// or for 3 frames if that is more than 3 seconds
const updateTimeout = Math.max(3000, 1000 / fps * 3);

let currentData = {};
let lastUpdateDate = Date.now();
const chartUpdateFunctions = [];

let mousePos = {};
window.addEventListener('mousemove', (event) => {
  mousePos = {
    x: event.clientX,
    y: event.clientY,
  };
});

const statusBadge = document.querySelector('.status-badge');
function setStatus(connected) {
  if (connected) {
    statusBadge.textContent = 'Connected';
    statusBadge.classList.add('connected');
  } else {
    statusBadge.textContent = 'Not Connected';
    statusBadge.classList.remove('connected');
  }
}
setStatus(true);

function setupMonitor(stat) {
  const categoryResolution = 100;
  const adaptiveMinPercentage = 0.8;
  const adaptiveMaxPercentage = 1.2;
  const {
    tag, maximum, minimum, color, history,
  } = stat;

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
  let tickPositions = [];
  let labelPositions = [];
  const rightAxis = {
    type: 'category',
    boundaryGap: true,
    axisLabel: {
      interval(y) {
        return labelPositions.includes(y);
      },
      textStyle: {
        color: 'black',
        fontFamily: 'Roboto Mono',
      },
    },
    axisTick: {
      alignWithLabel: true,
      interval(y) {
        return tickPositions.includes(y);
      },
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
  const options = {
    grid: {
      left: 60,
      top: 10,
      right: '5%',
      bottom: 10,
    },
    tooltip: {
      trigger: 'axis',
      triggerOn: 'none',
      formatter: tooltip => Math.round(tooltip[0].value[1] * 100) / 100,
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
        min: axisMin,
        max: axisMax,
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
          textStyle: {
            color: 'black',
            fontFamily: 'Roboto Mono',
          },
        },
      },
      rightAxis,
    ],
    color: [color],
    series: [{
      name: tag,
      symbol: 'none',
      type: 'line',
      showSymbol: false,
      hoverAnimation: false,
      data,
      animationEasingUpdate: 'linear',
      animationDurationUpdate: 1000 / fps,
      lineStyle: {
        width: 3,
      },
    }],
  };
  chart.setOption(options);

  let tooltipRepeater;
  const rect = chartElement.getBoundingClientRect();

  window.addEventListener('resize', () => {
    chart.setOption({
      animation: false
    });
    chart.resize();
    chart.setOption({
      animation: true
    });
  });

  chartElement.addEventListener('mouseover', (event) => {
    tooltipRepeater = setInterval(() => {
      chart.dispatchAction({
        type: 'showTip',
        x: (mousePos.x || event.clientX) - rect.x,
        y: (mousePos.y || event.clientY) - rect.y,
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
      tickPositions = [];
      labelPositions = [];
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
      rightAxis.data = contributorData;
    }
    chart.setOption({
      series: [{
        data,
      }],
      yAxis: [{}, rightAxis],
    });
  }
  chartUpdateFunctions.push(updateChart);
}

const request = new Request(`/stats`);
fetch(request).then(response => response.json()).then((stats) => {
  stats.forEach((stat) => {
    setupMonitor(stat);
  });
  setInterval(() => {
    const isConnected = Date.now() - lastUpdateDate < updateTimeout;
    setStatus(isConnected);
    if (isConnected) {
      chartUpdateFunctions.forEach(func => func());
    }
  }, 1000 / fps);
});

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

const removeStatBox = document.querySelector('.stat-remover select');
const addStatBox = document.querySelector('.stat-adder select');

document.querySelector('.stat-remover input[type="button"]').addEventListener('click', () => {
  data = {
    tag: removeStatBox.value,
  }
  const request = new Request(`/stats`, {
    'method': 'DELETE',
    'headers': {
      'Content-Type': 'application/json'
    },
    'body': JSON.stringify(data)
  });
  fetch(request).then((response) => {
    if(response.status != 200) {
      throw response.statusText;
    }
    return response;
  }).then((response) => response.json()).then((response) => {
    removeStatBox.querySelector(`option[value="${response.tag}"]`).remove();

    optionIndex = bisect(Array.from(addStatBox.children).map((x) => x.value), response.tag);
    const optionElement = document.createElement('option');
    optionElement.value = response.tag;
    optionElement.textContent = response.name;
    addStatBox.insertBefore(optionElement, addStatBox.children[optionIndex]);

    document.getElementById(response.tag).remove();
    window.dispatchEvent(new Event('resize'));
  }).catch((err) => console.error(err));
});

document.querySelector('.stat-adder input[type="button"]').addEventListener('click', () => {
  const data = {
    tag: addStatBox.value,
    settings: {}
  };
  const request = new Request(`/stats`, {
    'method': 'PUT',
    'headers': {
      'Content-Type': 'application/json'
    },
    'body': JSON.stringify(data)
  });
  fetch(request).then((response) => {
    if(response.status != 200) {
      throw response.statusText;
    }
    if(document.getElementById(data.tag)) {
      throw 'Stat already added.';
    }
    return response;
  }).then((response) => response.json()).then((response) => {
    addStatBox.querySelector(`option[value="${response.tag}"]`).remove();

    optionIndex = bisect(Array.from(removeStatBox.children).map((x) => x.value), response.tag);
    const optionElement = document.createElement('option');
    optionElement.value = response.tag;
    optionElement.textContent = response.name;
    removeStatBox.insertBefore(optionElement, removeStatBox.children[optionIndex]);

    const chart = document.createElement('div');
    chart.classList.add('chart-container');
    chart.id = response.tag;

    const childIds = Array.from(charts.children).map((child) => child.id);
    const index = bisect(childIds, chart.id);

    charts.insertBefore(chart, charts.children[index]);

    setupMonitor(response);
    window.dispatchEvent(new Event('resize'));
  }).catch((err) => console.error(err));

});

function bisect(array, key) {
  for(let i = 0; i < array.length; i++) {
    if(array[i] > key) {
      return i;
    }
  }
  return array.length - 1;
}