(() => {
  const button = document.querySelector('.copy-address');
  const address = document.getElementById('contact-address');
  const status = document.querySelector('.contact-copy-status');
  if (!button || !address || !status || !navigator.clipboard?.writeText) return;

  button.hidden = false;
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(address.textContent.trim());
      status.textContent = 'Email address copied.';
    } catch {
      status.textContent = 'Could not copy automatically. Select and copy the email address above.';
    }
  });
})();
