(() => {
  const controls = document.querySelector('.controls');
  const filter = document.getElementById('filter');
  const kind = document.getElementById('kind-filter');
  const count = document.getElementById('result-count');
  const items = [...document.querySelectorAll('.archive-item')].map(node => ({
    node, topics: JSON.parse(node.dataset.topics), kind: node.dataset.kind,
  }));
  if (!controls || !filter || !count || !items.length) return;
  function apply() {
    let visible = 0;
    for (const item of items) {
      const show = (!kind?.value || item.kind === kind.value) &&
        (!filter.value || item.topics.includes(filter.value));
      item.node.hidden = !show;
      if (show) visible++;
    }
    const noun = kind?.value || (kind ? 'result' : 'article');
    count.textContent = `${visible} ${noun}${visible === 1 ? '' : 's'}`;
  }
  filter.addEventListener('change', apply);
  kind?.addEventListener('change', apply);
  controls.hidden = false;
  apply();
})();
