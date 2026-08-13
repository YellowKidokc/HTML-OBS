/* ============================================================================
   HTMLNote panels — resizable Obsidian-style columns + add-ons snippet manager.
   ----------------------------------------------------------------------------
   Layout:  [ Files ] | preview | [ Add-ons ]
   - Draggable dividers with min/max clamping; widths persist to localStorage.
   - Double-click a divider to collapse/restore its column; the add-ons column
     also has a header toggle (◨).
   - Add-ons column is a CSS-snippet manager (the Obsidian snippet model): each
     snippet applies live to the HTMLNote interface and persists per browser.
   ========================================================================== */
(function () {
  'use strict';

  var LS = {
    sidebarW: 'htmlnote-sidebar-w',
    addonsW: 'htmlnote-addons-w',
    addonsOpen: 'htmlnote-addons-open',
    sidebarOpen: 'htmlnote-sidebar-open',
    snippets: 'htmlnote-addons'
  };

  var MIN = 180, MAX_FRAC = 0.6; // max = 60% of viewport

  function num(v, dflt) { var n = parseInt(v, 10); return isNaN(n) ? dflt : n; }
  function clampW(w) { return Math.max(MIN, Math.min(w, Math.round(window.innerWidth * MAX_FRAC))); }

  // ---- restore persisted widths / collapse state ----------------------------
  function restore() {
    var sidebar = document.getElementById('sidebar');
    var addons = document.getElementById('addons');
    var rRight = document.getElementById('resizer-right');

    var sw = localStorage.getItem(LS.sidebarW);
    if (sw) sidebar.style.width = clampW(num(sw, 300)) + 'px';
    var aw = localStorage.getItem(LS.addonsW);
    if (aw) addons.style.width = clampW(num(aw, 280)) + 'px';

    if (localStorage.getItem(LS.sidebarOpen) === '0') sidebar.style.display = 'none';
    // Add-ons default to CLOSED so the app opens clean; user opts in.
    var addonsOpen = localStorage.getItem(LS.addonsOpen) === '1';
    setAddons(addonsOpen);
  }

  function setAddons(open) {
    var addons = document.getElementById('addons');
    var rRight = document.getElementById('resizer-right');
    addons.classList.toggle('collapsed', !open);
    rRight.classList.toggle('hidden', !open);
    localStorage.setItem(LS.addonsOpen, open ? '1' : '0');
    var btn = document.getElementById('addons-toggle');
    if (btn) btn.setAttribute('aria-pressed', String(open));
  }

  // ---- drag-to-resize -------------------------------------------------------
  function initResizer(resizer) {
    var targetId = resizer.dataset.target;
    var invert = resizer.dataset.invert === '1';

    resizer.addEventListener('mousedown', function (e) {
      e.preventDefault();
      var target = document.getElementById(targetId);
      // If collapsed, a drag restores it first.
      if (targetId === 'sidebar' && target.style.display === 'none') {
        target.style.display = '';
        localStorage.setItem(LS.sidebarOpen, '1');
      }
      var startX = e.clientX;
      var startW = target.getBoundingClientRect().width;
      resizer.classList.add('dragging');
      document.body.classList.add('resizing');

      function onMove(ev) {
        var delta = ev.clientX - startX;
        var w = clampW(startW + (invert ? -delta : delta));
        target.style.width = w + 'px';
      }
      function onUp() {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        resizer.classList.remove('dragging');
        document.body.classList.remove('resizing');
        var finalW = Math.round(target.getBoundingClientRect().width);
        localStorage.setItem(targetId === 'sidebar' ? LS.sidebarW : LS.addonsW, finalW);
      }
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });

    // Double-click collapses / restores the target column.
    resizer.addEventListener('dblclick', function () {
      var target = document.getElementById(targetId);
      if (targetId === 'sidebar') {
        var hidden = target.style.display === 'none';
        target.style.display = hidden ? '' : 'none';
        localStorage.setItem(LS.sidebarOpen, hidden ? '1' : '0');
      } else {
        setAddons(target.classList.contains('collapsed'));
      }
    });
  }

  // ---- add-ons: CSS snippet manager ----------------------------------------
  var styleEl;
  function ensureStyleEl() {
    if (!styleEl) {
      styleEl = document.createElement('style');
      styleEl.id = 'addon-styles';
      document.head.appendChild(styleEl);
    }
    return styleEl;
  }

  function loadSnippets() {
    try { return JSON.parse(localStorage.getItem(LS.snippets)) || []; }
    catch (e) { return []; }
  }
  function saveSnippets(list) {
    try { localStorage.setItem(LS.snippets, JSON.stringify(list)); } catch (e) {}
  }

  var snippets = loadSnippets();
  var idSeq = 0;
  function newId() { return 'sn-' + Date.now() + '-' + (idSeq++); }

  function applySnippets() {
    var css = snippets.filter(function (s) { return s.enabled; })
      .map(function (s) { return '/* ' + (s.name || 'snippet') + ' */\n' + (s.css || ''); })
      .join('\n\n');
    ensureStyleEl().textContent = css;
  }

  function renderSnippets() {
    var body = document.getElementById('addons-body');
    if (!body) return;
    body.innerHTML = '';
    if (!snippets.length) {
      var empty = document.createElement('div');
      empty.className = 'addons-empty';
      empty.textContent = 'No add-ons yet. Add a CSS snippet to tweak the HTMLNote interface — e.g. `.tree-item { font-size: 14px; }`. Toggle it on to apply live.';
      body.appendChild(empty);
      return;
    }
    snippets.forEach(function (s) {
      var card = document.createElement('div');
      card.className = 'snippet' + (s.open ? ' open' : '');

      var head = document.createElement('div');
      head.className = 'snippet-head';

      var chk = document.createElement('input');
      chk.type = 'checkbox'; chk.checked = !!s.enabled;
      chk.title = 'Enable snippet';
      chk.addEventListener('change', function () { s.enabled = chk.checked; saveSnippets(snippets); applySnippets(); });

      var name = document.createElement('input');
      name.type = 'text'; name.value = s.name || ''; name.placeholder = 'Snippet name';
      name.addEventListener('input', function () { s.name = name.value; saveSnippets(snippets); if (s.enabled) applySnippets(); });

      var fold = document.createElement('button');
      fold.className = 'snippet-fold'; fold.textContent = s.open ? '▾' : '▸'; fold.title = 'Edit CSS';
      fold.addEventListener('click', function () {
        s.open = !s.open; card.classList.toggle('open', s.open); fold.textContent = s.open ? '▾' : '▸';
        saveSnippets(snippets);
      });

      var del = document.createElement('button');
      del.className = 'snippet-del'; del.textContent = '✕'; del.title = 'Delete snippet';
      del.addEventListener('click', function () {
        snippets = snippets.filter(function (x) { return x.id !== s.id; });
        saveSnippets(snippets); applySnippets(); renderSnippets();
      });

      head.appendChild(chk); head.appendChild(name); head.appendChild(fold); head.appendChild(del);

      var ta = document.createElement('textarea');
      ta.value = s.css || ''; ta.placeholder = '/* CSS */';
      ta.spellcheck = false;
      ta.addEventListener('input', function () { s.css = ta.value; saveSnippets(snippets); if (s.enabled) applySnippets(); });

      card.appendChild(head);
      card.appendChild(ta);
      body.appendChild(card);
    });
  }

  // ---- wiring ---------------------------------------------------------------
  function init() {
    restore();
    ['resizer-left', 'resizer-right'].forEach(function (id) {
      var r = document.getElementById(id);
      if (r) initResizer(r);
    });

    var toggle = document.getElementById('addons-toggle');
    if (toggle) toggle.addEventListener('click', function () {
      var addons = document.getElementById('addons');
      setAddons(addons.classList.contains('collapsed'));
    });

    var addBtn = document.getElementById('addon-new');
    if (addBtn) addBtn.addEventListener('click', function () {
      snippets.push({ id: newId(), name: 'New snippet', css: '', enabled: false, open: true });
      saveSnippets(snippets);
      renderSnippets();
    });

    // Re-clamp widths if the window shrinks below current pane sizes.
    window.addEventListener('resize', function () {
      ['sidebar', 'addons'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el && el.style.width) el.style.width = clampW(parseInt(el.style.width, 10)) + 'px';
      });
    });

    applySnippets();
    renderSnippets();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
