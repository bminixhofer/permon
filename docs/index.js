hljs.initHighlightingOnLoad();

document.querySelectorAll('.image-changer').forEach((elem) => {
    if(elem.classList.contains('selected')) {
        selectElement(elem);
    }
    elem.addEventListener('click', (event) => {
        selectElement(elem);
    });
});

function selectElement(elem) {
    const parent = document.querySelector(elem.dataset.target)
    const target = parent.children[parseInt(elem.dataset.child)];

    Array.from(parent.children).forEach((elem) => {
        elem.style.opacity = 0;
    })
    target.style.opacity = 1;

    parent.parentElement.querySelectorAll('.image-changer').forEach((elem) => {
        elem.classList.remove('selected');
    });
    elem.classList.add('selected');
}