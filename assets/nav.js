/* DFD CRRO Manual - Navigation */

// DFD patch favicon, same as the other DFD tool sites. Pages built by build_site.py already
// carry these tags; this covers any page that does not.
(function () {
  const ICON = 'https://files.constantcontact.com/3720c3fd901/10017eb4-f7d2-424d-92ed-c1b5424b9869.png';
  if (!document.querySelector('link[rel~="icon"]')) {
    [['icon', 'image/png'], ['apple-touch-icon', null]].forEach(([rel, type]) => {
      const l = document.createElement('link');
      l.rel = rel; l.href = ICON; if (type) l.type = type;
      document.head.appendChild(l);
    });
  }
})();
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.sidebar-overlay');

  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('open');
    });
  }

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('open');
    });
  }

  // Highlight active nav link
  const current = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href === current || (current === '' && href === 'index.html')) {
      link.classList.add('active');
      // Scroll sidebar to active link
      setTimeout(() => link.scrollIntoView({ block: 'center', behavior: 'instant' }), 50);
    }
  });
});
