import './style.scss';

hljs.initHighlightingOnLoad();

function selectElement(elem) {
  const parent = document.querySelector(elem.dataset.target);
  const target = parent.children[parseInt(elem.dataset.child, 10)];

  for (let i = 0; i < parent.children.length; i += 1) {
    parent.children[i].style.opacity = 0;
  }
  target.style.opacity = 1;

  parent.parentElement.querySelectorAll('.image-changer').forEach((button) => {
    button.classList.remove('selected');
  });
  elem.classList.add('selected');
}


document.querySelectorAll('.image-changer').forEach((elem) => {
  if (elem.classList.contains('selected')) {
    selectElement(elem);
  }
  elem.addEventListener('click', () => {
    selectElement(elem);
  });
});
