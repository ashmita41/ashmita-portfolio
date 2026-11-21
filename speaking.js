(() => {
  const carousel = document.querySelector('[data-speaking-carousel]');
  if (!carousel) return;

  const rail = carousel.querySelector('.talk-track');
  const cards = [...rail.children];
  const controls = carousel.querySelector('.talk-controls');
  const prev = carousel.querySelector('[data-talk-prev]');
  const next = carousel.querySelector('[data-talk-next]');
  const dots = carousel.querySelector('.talk-dots');
  const position = carousel.querySelector('.talk-position');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let stops = [], active = 0, settle;

  function update() {
    active = stops.reduce((best, stop, index) =>
      Math.abs(stop - rail.scrollLeft) < Math.abs(stops[best] - rail.scrollLeft) ? index : best, 0);
    prev.setAttribute('aria-disabled', String(active === 0));
    next.setAttribute('aria-disabled', String(active === stops.length - 1));
    [...dots.children].forEach((dot, i) => dot.classList.toggle('active', i === active));
    const text = `${active + 1} of ${stops.length}`;
    if (position.textContent !== text) position.textContent = text;
  }

  function measure() {
    const max = Math.max(0, rail.scrollWidth - rail.clientWidth);
    const start = cards[0].getBoundingClientRect().left;
    stops = [...new Set(cards.map(card =>
      Math.min(max, Math.round(card.getBoundingClientRect().left - start))))];
    if (dots.children.length !== stops.length) {
      dots.replaceChildren(...stops.map(() => {
        const dot = document.createElement('span');
        dot.className = 'talk-dot';
        return dot;
      }));
    }
    controls.hidden = stops.length < 2;
    update();
  }

  function go(index) {
    if (index < 0 || index >= stops.length) return;
    rail.scrollTo({ left: stops[index], behavior: reducedMotion.matches ? 'instant' : 'smooth' });
  }

  prev.addEventListener('click', () => go(active - 1));
  next.addEventListener('click', () => go(active + 1));
  rail.addEventListener('scroll', () => {
    clearTimeout(settle);
    settle = setTimeout(update, 100);
  }, { passive: true });
  rail.addEventListener('keydown', event => {
    if (event.target !== rail || event.altKey || event.metaKey || event.ctrlKey || event.shiftKey) return;
    const keys = { ArrowLeft: active - 1, ArrowRight: active + 1, Home: 0, End: stops.length - 1 };
    if (!Object.hasOwn(keys, event.key)) return;
    event.preventDefault();
    go(keys[event.key]);
  });
  if (typeof ResizeObserver === 'function') new ResizeObserver(measure).observe(rail);
  else window.addEventListener('resize', measure);
  measure();
})();
