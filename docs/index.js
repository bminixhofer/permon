hljs.initHighlightingOnLoad();

document.querySelectorAll('.image-changer').forEach((elem) => {
    elem.addEventListener('click', (event) => {
        document.querySelector(elem.dataset.target).src = elem.dataset.url;
        elem.parentElement.querySelectorAll('.image-changer').forEach((elem) => {
            elem.classList.remove('selected');
        });
        elem.classList.add('selected');
    });
});