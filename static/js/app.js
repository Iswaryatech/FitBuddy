(function () {
  // --- Day route: pick a day, keyboard friendly -------------------------
  var route = document.querySelector('[data-route]');
  if (route) {
    var tabs = Array.prototype.slice.call(route.querySelectorAll('[role=tab]'));
    var panels = Array.prototype.slice.call(document.querySelectorAll('[data-panel]'));

    function select(i, focus, setHash) {
      tabs.forEach(function (t, n) {
        var on = n === i;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.tabIndex = on ? 0 : -1;
      });
      panels.forEach(function (p, n) { p.hidden = n !== i; });
      if (focus) tabs[i].focus();
      if (setHash && history.replaceState) history.replaceState(null, '', '#day-' + i);
    }

    var today = (new Date().getDay() + 6) % 7; // Monday = 0
    var mark = tabs[today] && tabs[today].querySelector('.today-mark');
    if (mark) { mark.hidden = false; }

    var start = today;
    var m = /^#day-(\d)$/.exec(location.hash);
    if (m && tabs[+m[1]]) start = +m[1];

    tabs.forEach(function (t, n) {
      t.addEventListener('click', function () { select(n, false, true); });
      t.addEventListener('keydown', function (e) {
        var next = null;
        if (e.key === 'ArrowRight') next = (n + 1) % tabs.length;
        if (e.key === 'ArrowLeft') next = (n + tabs.length - 1) % tabs.length;
        if (e.key === 'Home') next = 0;
        if (e.key === 'End') next = tabs.length - 1;
        if (next !== null) { e.preventDefault(); select(next, true, true); }
      });
    });
    select(start, false, false);
  }

  // --- Quick feedback suggestions ---------------------------------------
  document.querySelectorAll('[data-fill]').forEach(function (b) {
    b.addEventListener('click', function () {
      var box = document.getElementById('feedback');
      if (!box) return;
      var add = b.getAttribute('data-fill');
      box.value = box.value.trim() ? box.value.trim().replace(/[.]$/, '') + '. ' + add : add;
      box.focus();
    });
  });

  // --- Busy state on slow submits (Gemini can take a few seconds) --------
  document.querySelectorAll('form[data-busy-text]').forEach(function (f) {
    f.addEventListener('submit', function () {
      var btn = f.querySelector('button[type=submit]');
      if (btn && f.checkValidity()) {
        btn.disabled = true;
        btn.textContent = f.getAttribute('data-busy-text');
      }
    });
  });

  // --- Confirm destructive actions --------------------------------------
  document.querySelectorAll('form[data-confirm]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      if (!window.confirm(f.getAttribute('data-confirm'))) e.preventDefault();
    });
  });
})();
