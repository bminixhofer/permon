import './sass/main.scss';
import { setupSocket, setupMonitors } from './monitors';
import setupSettings from './settings';
import { setStatus } from './status';


const currentStatsRequest = new Request('/stats');
const allStatsRequest = new Request('/allStats');

fetch(currentStatsRequest).then(response => response.json()).then((stats) => {
  setupMonitors(stats);
});

fetch(allStatsRequest).then(response => response.json()).then((stats) => {
  setupSettings(stats);
});

setupSocket();
setStatus(true);
