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

// Hamburger toggle for the collapsed mobile nav (see the max-width: 860px
// rule in style.css). The menu also auto-closes if the window is resized
// past the breakpoint, so it can't be left open-but-hidden on desktop.
function initNavToggle() {
  var toggle = document.querySelector('.nav-toggle');
  var navbar = document.getElementById('main-navbar');
  if (!toggle || !navbar) return;

  toggle.addEventListener('click', function () {
    var isOpen = navbar.classList.toggle('nav-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
  });

  var staysOpen = window.matchMedia('(min-width: 861px)');
  staysOpen.addEventListener('change', function (e) {
    if (e.matches) {
      navbar.classList.remove('nav-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
}

// Auto-disables a .form-btn once its order/shop window has passed, e.g. a
// monthly popcorn or Spirit Shop link. Add data-cutoff="YYYY-MM-DDTHH:MM:SS"
// (local time) to a button to opt it in - update that value alongside the
// href each time the link changes, and disabling resets itself with it.
// Buttons with no data-cutoff (like the evergreen spirit wear link) are
// left alone.
function initDatedButtons() {
  var now = new Date();
  document.querySelectorAll('.form-btn[data-cutoff]').forEach(function (btn) {
    var cutoff = new Date(btn.getAttribute('data-cutoff'));
    if (isNaN(cutoff) || now < cutoff) return;
    btn.removeAttribute('href');
    btn.removeAttribute('target');
    btn.setAttribute('aria-disabled', 'true');
    btn.addEventListener('click', function (e) { e.preventDefault(); });
    var hidden = btn.querySelector('.visually-hidden');
    if (hidden) hidden.textContent = ' (closed)';
  });
}

// Keeps the footer's copyright year current without anyone having to edit
// it every January.
function initFooterYear() {
  var el = document.getElementById('footer-year');
  if (el) el.textContent = new Date().getFullYear();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDropdowns);
  document.addEventListener('DOMContentLoaded', initNavToggle);
  document.addEventListener('DOMContentLoaded', initDatedButtons);
  document.addEventListener('DOMContentLoaded', initFooterYear);
} else {
  initDropdowns();
  initNavToggle();
  initDatedButtons();
  initFooterYear();
}
