// Исходные ссылки остаются пригодными для просмотра Markdown на GitHub.
document.querySelectorAll('main a[href]').forEach((link) => {
  const href = link.getAttribute('href');
  if (!href || /^(?:[a-z][a-z\d+.-]*:|\/|#)/i.test(href)) return;
  if (href === '../README.md') link.setAttribute('href', '../');
  else if (/\.md(?:#|$)/i.test(href)) link.setAttribute('href', href.replace(/\.md(?=#|$)/i, '.html'));
});
