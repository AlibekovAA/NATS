export function initializeTitleAnimation() {
    const title = document.querySelector('.animated-title span');
    if (!title) return;

    const text = title.textContent || '';
    const fragment = document.createDocumentFragment();

    requestAnimationFrame(() => {
        title.textContent = '';

        text.split('').forEach((char, i) => {
            const span = document.createElement('span');
            span.textContent = char;
            span.style.setProperty('--char-index', i + 1);
            fragment.appendChild(span);
        });

        title.appendChild(fragment);
    });
}
