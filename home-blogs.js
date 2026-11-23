(() => {
  'use strict';
  const track = document.getElementById('home-blog-track');
  if (!track) return;
  const slides = [...track.children];
  const controls = document.querySelector('[data-blog-controls]');
  if (!slides.length || !controls) return;

  const previous = controls.querySelector('[data-blog-prev]');
  const next = controls.querySelector('[data-blog-next]');
  const status = controls.querySelector('[role="status"]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let starts = [], widths = [], stops = [], target = null, settle;

  function sync() {
    const left = track.scrollLeft;
    const right = left + track.clientWidth;
    previous.setAttribute('aria-disabled', String(left <= 1));
    next.setAttribute('aria-disabled', String(left >= stops.at(-1) - 1));
    const visible = starts.reduce((list, start, i) => {
      const overlap = Math.min(right, start + widths[i]) - Math.max(left, start);
      if (overlap >= widths[i] / 2) list.push(i + 1);
      return list;
    }, []);
    const first = visible[0] || 1;
    const last = visible.at(-1) || first;
    const message = first === last ? `${first} of ${slides.length}` : `${first}–${last} of ${slides.length}`;
    if (status.textContent !== message) status.textContent = message;
  }

  function measure() {
    const max = Math.max(0, track.scrollWidth - track.clientWidth);
    const boxes = slides.map(slide => slide.getBoundingClientRect());
    starts = boxes.map(box => box.left - boxes[0].left);
    widths = boxes.map(box => box.width);
    stops = [...new Set(starts.map(start => Math.min(max, Math.round(start))))];
    controls.hidden = max < 2;
    target = null;
    sync();
  }

  function go(left) {
    if (left == null) return;
    target = left;
    track.scrollTo({ left, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
  }

  function advance(step) {
    const left = target ?? track.scrollLeft;
    go(step > 0
      ? stops.find(stop => stop > left + 1)
      : stops.findLast(stop => stop < left - 1));
  }

  previous.addEventListener('click', () => advance(-1));
  next.addEventListener('click', () => advance(1));
  track.addEventListener('scroll', () => {
    clearTimeout(settle);
    settle = setTimeout(() => { target = null; sync(); }, 120);
  }, { passive: true });
  for (const event of ['pointerdown', 'wheel']) {
    track.addEventListener(event, () => { target = null; }, { passive: true });
  }
  track.addEventListener('keydown', event => {
    if (event.target !== track || event.altKey || event.metaKey || event.ctrlKey || event.shiftKey || controls.hidden) return;
    const action = {
      ArrowLeft: () => advance(-1), ArrowRight: () => advance(1),
      Home: () => go(0), End: () => go(stops.at(-1)),
    }[event.key];
    if (!action) return;
    event.preventDefault();
    action();
  });
  if (typeof ResizeObserver === 'function') new ResizeObserver(measure).observe(track);
  else window.addEventListener('resize', measure);
  measure();
})();
