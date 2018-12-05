import { setupMonitor } from './monitors';
import { setErrorMessage, clearErrorMessage } from './status';

const charts = document.querySelector('.charts');
const settingsElement = document.querySelector('.settings');
const settingsToggle = document.querySelector('#settings-toggle');
const settingsToggleLabel = document.querySelector('.settings-toggle-label');
const removeStatBox = document.querySelector('.stat-remover select');
const removeStatButton = document.querySelector('.stat-remover input');
const addStatBox = document.querySelector('.stat-adder select');
const addStatButton = document.querySelector('.stat-adder input');
const statSettingsDiv = document.querySelector('.stat-settings');

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
      select.dispatchEvent(new Event('change'));

      // add the element to the other combo box
      const optionIndex = bisect(Array.from(otherSelect.children).map(x => x.value), response.tag);
      const optionElement = document.createElement('option');
      optionElement.value = response.tag;
      optionElement.textContent = response.name;
      otherSelect.insertBefore(optionElement, otherSelect.children[optionIndex]);
      otherSelect.dispatchEvent(new Event('change'));

      doneCallback(response);

      // after a monitor has been added / removed the size of the others changes
      // so emit a resize event even though the browser window has stayed the same size
      window.dispatchEvent(new Event('resize'));
      clearErrorMessage();
    })
      .catch(async (response) => {
        const text = await response.text();
        setErrorMessage(text);
      });
  });
  select.dispatchEvent(new Event('change'));
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
const addRequestCallback = () => {
  const settings = {};
  statSettingsDiv.querySelectorAll('input[type="text"]').forEach((element) => {
    settings[element.dataset.key] = element.value;
  });
  return new Request('/stats', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      tag: addStatBox.value,
      settings,
    }),
  });
};

function setupStatSettings(select, stats) {
  select.addEventListener('change', () => {
    const selectedOption = select.options[select.selectedIndex];
    const { settings } = stats[selectedOption.value];

    // remove all previous children
    statSettingsDiv.innerHTML = '';
    Object.entries(settings).forEach(([key, value]) => {
      const id = `setting-${key}`;

      const element = document.createElement('input');
      element.type = 'text';
      element.id = id;
      element.dataset.key = key;
      element.value = value;

      const label = document.createElement('label');
      label.textContent = key;
      label.for = id;

      const container = document.createElement('div');
      container.classList.add('stat-setting');
      container.appendChild(label);
      container.appendChild(element);

      statSettingsDiv.append(container);
    });
  });
}

export default function setupSettings(stats) {
  window.addEventListener('click', (event) => {
    // when clicking outside of the settings drawer, make it close
    if (![settingsToggle, settingsToggleLabel].includes(event.target)
        && !settingsElement.contains(event.target)) {
      settingsToggle.checked = false;
    }
  });

  setupStatSettings(addStatBox, stats);
  setupChangeStat(removeStatButton, removeStatBox, addStatBox, removeRequestCallback, (res) => {
    document.getElementById(res.tag).remove();
  });
  setupChangeStat(addStatButton, addStatBox, removeStatBox, addRequestCallback, (res) => {
    const chart = document.createElement('div');
    chart.classList.add('chart-container');
    chart.id = res.tag;

    const childIds = Array.from(charts.children).map(child => child.id);
    // make sure that the monitor stay in alphabetical order
    const index = bisect(childIds, chart.id);
    charts.insertBefore(chart, charts.children[index]);

    setupMonitor(res);
  });
}
