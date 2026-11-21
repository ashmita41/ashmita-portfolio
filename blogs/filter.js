(() => {
  const controls = document.querySelector('.controls');
  const filter = document.getElementById('filter');
  const count = document.getElementById('result-count');
  const items = [...document.querySelectorAll('.archive-item')];
  if (!controls || !filter || !count || !items.length) return;
  function apply() {
    let visible = 0;
    for (const item of items) {
      const show = !filter.value || JSON.parse(item.dataset.topics).includes(filter.value);
      item.hidden = !show;
      if (show) visible++;
    }
    count.textContent = `${visible} ${visible === 1 ? 'article' : 'articles'}`;
  }
  filter.addEventListener('change', apply);
  controls.hidden = false;
  apply();
})();
