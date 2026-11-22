(() => {
  'use strict';
  const key = 'ashmita-color-theme';
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let choice = null;
  let button;
  try {
    const value = localStorage.getItem(key);
    if (value === 'light' || value === 'dark') choice = value;
  } catch (_) { /* Private or restricted storage: still allow this page to switch. */ }

  function apply() {
    const dark = choice ? choice === 'dark' : system.matches;
    root.dataset.theme = dark ? 'dark' : 'light';
    if (button) button.setAttribute('aria-pressed', String(dark));
    return dark;
  }

  apply(); // This script runs before paint, including on direct blog visits.
  if (typeof system.addEventListener === 'function') system.addEventListener('change', apply);
  else if (typeof system.addListener === 'function') system.addListener(apply);
  document.addEventListener('DOMContentLoaded', () => {
    button = document.querySelector('[data-theme-toggle]');
    if (!button) return;
    apply();
    button.hidden = false;
    button.addEventListener('click', () => {
      choice = apply() ? 'light' : 'dark';
      try { localStorage.setItem(key, choice); } catch (_) { /* Keep the in-page choice. */ }
      apply();
    });
  }, { once:true });
  window.addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    choice = event.newValue === 'light' || event.newValue === 'dark' ? event.newValue : null;
    apply();
  });
})();
