(() => {
  'use strict';
  const archive = document.querySelector('.blog-archive');
  if (!archive) return;
  const controls = archive.querySelector('.archive-controls');
  const types = [...archive.querySelectorAll('.archive-types button')];
  const filter = archive.querySelector('#filter');
  const search = archive.querySelector('#archive-search');
  const resultBar = archive.querySelector('.archive-results-bar');
  const count = archive.querySelector('#result-count');
  const clear = archive.querySelector('.archive-clear');
  const empty = archive.querySelector('.archive-empty');
  const more = archive.querySelector('.archive-more');
  const moreButton = more.querySelector('button');
  const pageSize = 9;
  const normalize = value => value.normalize('NFKC').toLowerCase().trim();
  const items = [...archive.querySelectorAll('.archive-item')].map(node => {
    const topics = JSON.parse(node.dataset.topics);
    return {
      node, topics, kind: node.dataset.kind,
      text: normalize([node.querySelector('h3').textContent, ...topics].join(' ')),
    };
  });
  if (!items.length) return;

  let kind = 'article';
  let shown = pageSize;
  function readUrl() {
    const { searchParams, hash } = new URL(window.location.href);
    const anchor = hash.startsWith('#') && items.find(item => `#${item.node.id}` === hash);
    kind = (types.length && searchParams.get('type') === 'post') ? 'post' : 'article';
    const topic = searchParams.get('topic');
    filter.value = [...filter.options].some(option => option.value === topic) ? topic : '';
    search.value = searchParams.get('q') || '';
    const limit = Number(searchParams.get('shown'));
    shown = Number.isSafeInteger(limit) ? Math.max(pageSize, Math.min(limit, items.length)) : pageSize;
    if (anchor && !searchParams.has('type') && !searchParams.has('topic') && !searchParams.has('q')) {
      kind = anchor.kind;
      const position = items.filter(item => item.kind === kind).indexOf(anchor);
      shown = Math.max(shown, Math.ceil((position + 1) / pageSize) * pageSize);
    }
    return anchor;
  }

  function saveUrl() {
    const url = new URL(window.location.href);
    const state = {
      type: kind === 'post' ? 'post' : '',
      topic: filter.value,
      q: search.value.trim(),
      shown: shown > pageSize ? shown : '',
    };
    for (const [key, value] of Object.entries(state)) {
      if (value) url.searchParams.set(key, value);
      else url.searchParams.delete(key);
    }
    // The Archive works from a file too, where some browsers disallow URL updates.
    try { window.history.replaceState(null, '', url); } catch (_) { /* no shareable URL */ }
  }

  function render() {
    const terms = normalize(search.value).split(/\s+/).filter(Boolean);
    const found = [];
    for (const item of items) {
      const isMatch = item.kind === kind && (!filter.value || item.topics.includes(filter.value)) &&
        terms.every(term => item.text.includes(term));
      if (isMatch) found.push(item);
      item.node.hidden = !isMatch || found.length > shown;
    }
    for (const button of types) button.setAttribute('aria-pressed', String(button.dataset.kind === kind));
    const noun = found.length === 1 ? kind : `${kind}s`;
    const showing = Math.min(shown, found.length);
    count.textContent = found.length > showing ? `Showing ${showing} of ${found.length} ${noun}` : `${found.length} ${noun}`;
    clear.hidden = !filter.value && !terms.length;
    empty.hidden = found.length > 0;
    more.hidden = found.length <= shown;
    return found;
  }

  function update() {
    shown = pageSize;
    render();
    saveUrl();
  }

  for (const button of types) button.addEventListener('click', () => {
    if (kind === button.dataset.kind) return;
    kind = button.dataset.kind;
    // Keep search text for comparison, but an irrelevant topic can hide the
    // entire destination tab. Only retain the topic if it exists there.
    if (filter.value && !items.some(item => item.kind === kind && item.topics.includes(filter.value))) filter.value = '';
    update();
  });
  search.addEventListener('input', update);
  filter.addEventListener('change', update);
  controls.addEventListener('submit', event => event.preventDefault());
  clear.addEventListener('click', () => {
    search.value = '';
    filter.value = '';
    update();
    search.focus();
  });
  moreButton.addEventListener('click', () => {
    const previous = shown;
    shown += pageSize;
    const revealed = render()[previous];
    saveUrl();
    const card = revealed?.node.querySelector('.archive-card');
    if (card?.matches('a')) card.focus();
    else if (card) {
      card.tabIndex = -1;
      card.focus();
    }
  });
  window.addEventListener('popstate', () => {
    readUrl();
    render();
  });
  const anchor = readUrl();
  render();
  controls.hidden = resultBar.hidden = false;
  if (anchor && !anchor.node.hidden) anchor.node.scrollIntoView();
})();
