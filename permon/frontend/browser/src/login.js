import { sha256 } from 'js-sha256';

const form = document.querySelector('.login-form');
const passwordInput = document.querySelector('.login-form input[name="password"]');
const errorMessage = document.querySelector('.login-form .error-message');

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const request = new Request('/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      password: sha256(passwordInput.value),
    }),
  });
  fetch(request).then(async (response) => {
    if (response.status === 200) {
      window.location.replace(response.url);
    } else {
      const text = await response.text();
      errorMessage.textContent = text;
    }
  });
});
