const statusBadge = document.querySelector('.status-badge');
const errorMessage = document.querySelector('.error-message');

export function setStatus(connected) {
  if (connected) {
    statusBadge.textContent = 'Connected';
    statusBadge.classList.add('connected');
  } else {
    statusBadge.textContent = 'Not Connected';
    statusBadge.classList.remove('connected');
  }
}

export function setErrorMessage(message) {
  errorMessage.textContent = `Error: ${message}`;
}

export function clearErrorMessage() {
  errorMessage.textContent = '';
}