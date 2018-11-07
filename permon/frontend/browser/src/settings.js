import { setupMonitor } from './monitors';

const charts = document.querySelector('.charts');
const removeStatBox = document.querySelector('.stat-remover select');
const addStatBox = document.querySelector('.stat-adder select');

function bisect(array, key) {
  for (let i = 0; i < array.length; i += 1) {
    if (array[i] > key) {
      return i;
    }
  }
  return array.length - 1;
}

function setupChangeStat(select, otherSelect, requestCallback, doneCallback) {
  select.addEventListener('click', () => {
    const request = requestCallback();
    fetch(request).then((response) => {
      if (response.status !== 200) {
        throw response.statusText;
      }
      return response;
    }).then(response => response.json()).then((response) => {
      // remove the element from the current combo box
      select.querySelector(`option[value="${response.tag}"]`).remove();

      // add the element to the other combo box
      const optionIndex = bisect(Array.from(otherSelect.children).map(x => x.value), response.tag);
      const optionElement = document.createElement('option');
      optionElement.value = response.tag;
      optionElement.textContent = response.name;
      otherSelect.insertBefore(optionElement, otherSelect.children[optionIndex]);

      doneCallback(response);

      window.dispatchEvent(new Event('resize'));
    })
      .catch();
  });
}

const removeRequestCallback = () => new Request('/stats', {
  method: 'DELETE',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    tag: removeStatBox.value,
  }),
});
const addRequestCallback = () => new Request('/stats', {
  method: 'DELETE',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    tag: addStatBox.value,
    settings: {},
  }),
});

export default function setupSettings() {
  setupChangeStat(removeStatBox, addStatBox, removeRequestCallback, (response) => {
    document.getElementById(response.tag).remove();
  });
  setupChangeStat(addStatBox, removeStatBox, addRequestCallback, (response) => {
    const chart = document.createElement('div');
    chart.classList.add('chart-container');
    chart.id = response.tag;

    const childIds = Array.from(charts.children).map(child => child.id);
    const index = bisect(childIds, chart.id);

    charts.insertBefore(chart, charts.children[index]);

    setupMonitor(response);
  });
}
