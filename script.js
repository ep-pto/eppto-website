// Dropdown menus open on hover for mouse users. Touch devices have no hover,
// so the parent link toggles the menu on tap instead of following its href.
function initDropdowns() {
  var parents = document.querySelectorAll('.has-dropdown');
  var canHover = window.matchMedia('(hover: hover)');

  function closeAll(except) {
    parents.forEach(function (li) {
      if (li !== except) {
        li.classList.remove('open');
        li.querySelector(':scope > .nav-link').setAttribute('aria-expanded', 'false');
      }
    });
  }

  parents.forEach(function (li) {
    var link = li.querySelector(':scope > .nav-link');
    link.setAttribute('aria-haspopup', 'true');
    link.setAttribute('aria-expanded', 'false');

    link.addEventListener('click', function (e) {
      if (canHover.matches) return; // mouse users keep hover behaviour
      e.preventDefault();
      var isOpen = li.classList.contains('open');
      closeAll(li);
      li.classList.toggle('open', !isOpen);
      link.setAttribute('aria-expanded', String(!isOpen));
    });
  });

  // Tapping anywhere outside an open menu closes it.
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.has-dropdown')) closeAll(null);
  });

  // Escape closes any open menu.
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeAll(null);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDropdowns);
} else {
  initDropdowns();
}
