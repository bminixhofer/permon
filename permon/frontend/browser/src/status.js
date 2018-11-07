const statusBadge = document.querySelector('.status-badge');

export default function setStatus(connected) {
  if (connected) {
    statusBadge.textContent = 'Connected';
    statusBadge.classList.add('connected');
  } else {
    statusBadge.textContent = 'Not Connected';
    statusBadge.classList.remove('connected');
  }
}
