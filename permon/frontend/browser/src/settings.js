import { setupMonitor } from './monitors';
import { setErrorMessage, clearErrorMessage } from './status';

const charts = document.querySelector('.charts');
const removeStatBox = document.querySelector('.stat-remover select');
const removeStatButton = document.querySelector('.stat-remover input');
const addStatBox = document.querySelector('.stat-adder select');
const addStatButton = document.querySelector('.stat-adder input');

function bisect(array, key) {
  for (let i = 0; i < array.length; i += 1) {
    if (array[i] > key) {
      return i;
    }
  }
  return array.length - 1;
}

function setupChangeStat(button, select, otherSelect, requestCallback, doneCallback) {
  button.addEventListener('click', () => {
    const request = requestCallback();
    fetch(request).then((response) => {
      if (response.status !== 200) {
        throw response;
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
      clearErrorMessage();
    })
      .catch(async (response) => {
        const text = await response.text();
        setErrorMessage(text);
      });
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
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    tag: addStatBox.value,
    settings: {},
  }),
});

export default function setupSettings() {
  setupChangeStat(removeStatButton, removeStatBox, addStatBox, removeRequestCallback, (res) => {
    document.getElementById(res.tag).remove();
  });
  setupChangeStat(addStatButton, addStatBox, removeStatBox, addRequestCallback, (res) => {
    const chart = document.createElement('div');
    chart.classList.add('chart-container');
    chart.id = res.tag;

    const childIds = Array.from(charts.children).map(child => child.id);
    const index = bisect(childIds, chart.id);

    charts.insertBefore(chart, charts.children[index]);

    setupMonitor(res);
  });
}
