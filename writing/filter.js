(() => {
  const filters = document.querySelector('.article-filters');
  const status = document.getElementById('archive-status');
  const groups = Array.from(document.querySelectorAll('.archive-group'));
  const cards = Array.from(document.querySelectorAll('.article-card'));
  if (!filters || !status || !cards.length) return;

  function show(value) {
    let count = 0;
    cards.forEach(card => {
      const visible = value === 'all' || card.dataset.tags.split(' ').includes(value);
      card.hidden = !visible;
      if (visible) count++;
    });
    groups.forEach(group => { group.hidden = !group.querySelector('.article-card:not([hidden])'); });
    filters.querySelectorAll('button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.filter === value));
    });
    status.textContent = `Showing ${count} ${count === 1 ? 'article' : 'articles'}`;
  }

  filters.addEventListener('click', event => {
    const button = event.target.closest('button[data-filter]');
    if (button && filters.contains(button)) show(button.dataset.filter);
  });
  filters.hidden = false;
  status.hidden = false;
  show('all');
})();
