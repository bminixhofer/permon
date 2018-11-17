import { setupSocket, setupMonitors } from './monitors';
import setupSettings from './settings';
import { setStatus } from './status';

setupSocket();
setupMonitors();
setupSettings();

setStatus(true);
