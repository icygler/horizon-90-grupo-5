export function nextSlideIndex(currentIndex, direction, totalSlides) {
  return Math.min(Math.max(currentIndex + direction, 0), totalSlides - 1);
}

function mountPitchDeck(root) {
  if (!root) return;
  const slides = [...root.querySelectorAll('[data-slide]')];
  const previous = root.querySelector('[data-deck-previous]');
  const next = root.querySelector('[data-deck-next]');
  const counter = root.querySelector('[data-deck-counter]');
  const progress = root.querySelector('[data-deck-progress]');
  let activeIndex = 0;

  function render() {
    slides.forEach((slide, index) => {
      const active = index === activeIndex;
      slide.classList.toggle('is-active', active);
      slide.setAttribute('aria-hidden', String(!active));
    });
    counter.textContent = String(activeIndex + 1);
    progress.style.width = `${((activeIndex + 1) / slides.length) * 100}%`;
    previous.disabled = activeIndex === 0;
    next.disabled = activeIndex === slides.length - 1;
  }

  function move(direction) {
    const nextIndex = nextSlideIndex(activeIndex, direction, slides.length);
    if (nextIndex === activeIndex) return;
    activeIndex = nextIndex;
    render();
  }

  previous.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  window.addEventListener('keydown', (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key === 'ArrowRight') move(1);
    if (event.key === 'ArrowLeft') move(-1);
    if (event.key === 'Home') { activeIndex = 0; render(); }
    if (event.key === 'End') { activeIndex = slides.length - 1; render(); }
  });
  root.classList.add('deck-ready');
  render();
}

if (typeof document !== 'undefined') {
  mountPitchDeck(document.querySelector('[data-deck]'));
}
