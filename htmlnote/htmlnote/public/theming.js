/* ============================================================================
   HTMLNote theming — the "two-surface" customization system.
   ----------------------------------------------------------------------------
   Surface 1 (structural): light/dark/contrast theme + comfortable/compact
     density, applied as data-theme / data-density attributes on :root.
     Handled inline in index.html.
   Surface 2 (cosmetic): this file. A Style-Settings-style GUI bound ONLY to a
     whitelist of documented semantic tokens (THEMEABLE below). User values are
     written as inline custom properties on :root (which win over the stylesheet
     default), persisted to localStorage, and are exportable/importable as a
     portable theme package. Nothing structural (spacing, panel sizes, layout)
     is exposed, so a user theme can never break the UI.
   ========================================================================== */
(function () {
  'use strict';

  var STORAGE_KEY = 'htmlnote-theme-overrides';

  // The whitelist. `var` MUST be a semantic token from design-system.css.
  var THEMEABLE = [
    {
      group: 'Accent',
      controls: [
        { var: '--accent-h', label: 'Hue',        kind: 'range', min: 0, max: 360, step: 1, unit: '' },
        { var: '--accent-s', label: 'Saturation', kind: 'range', min: 0, max: 100, step: 1, unit: '%' },
        { var: '--accent-l', label: 'Lightness',  kind: 'range', min: 0, max: 100, step: 1, unit: '%' }
      ]
    },
    {
      group: 'Colors',
      controls: [
        { var: '--background-primary',   label: 'Background',     kind: 'color' },
        { var: '--background-secondary', label: 'Sidebar',        kind: 'color' },
        { var: '--background-elevated',  label: 'Elevated',       kind: 'color' },
        { var: '--text-normal',          label: 'Text',           kind: 'color' },
        { var: '--text-muted',           label: 'Muted text',     kind: 'color' },
        { var: '--border-subtle',        label: 'Borders',        kind: 'color' }
      ]
    },
    {
      group: 'Typography',
      controls: [
        {
          var: '--font-text-theme', label: 'Reading font', kind: 'select', options: [
            { label: 'Geist / Inter',  value: '"Geist","Inter",ui-sans-serif,system-ui,sans-serif' },
            { label: 'System UI',      value: 'system-ui,-apple-system,"Segoe UI",Roboto,sans-serif' },
            { label: 'Serif',          value: '"Lyon-Text",Georgia,ui-serif,serif' },
            { label: 'Monospace',      value: 'ui-monospace,"Geist Mono",Consolas,monospace' }
          ]
        },
        { var: '--font-size-body',      label: 'Body size',    kind: 'range', min: 13, max: 20,  step: 1,   unit: 'px' },
        { var: '--line-height-reading', label: 'Line height',  kind: 'range', min: 1.3, max: 1.9, step: 0.05, unit: '' }
      ]
    },
    {
      group: 'Shape',
      controls: [
        { var: '--radius-m', label: 'Corner radius', kind: 'range', min: 0, max: 16, step: 1, unit: 'px' }
      ]
    }
  ];

  var WHITELIST = THEMEABLE.reduce(function (set, g) {
    g.controls.forEach(function (c) { set[c.var] = c; });
    return set;
  }, {});

  var root = document.documentElement;

  // ---- persistence -------------------------------------------------------
  function loadOverrides() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      var obj = raw ? JSON.parse(raw) : {};
      // Defensive: only keep whitelisted keys (protects against tampered/old data).
      var clean = {};
      Object.keys(obj).forEach(function (k) { if (WHITELIST[k]) clean[k] = obj[k]; });
      return clean;
    } catch (e) { return {}; }
  }

  function saveOverrides(o) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(o)); } catch (e) {}
  }

  var overrides = loadOverrides();

  function applyOverride(name, value) {
    if (!WHITELIST[name]) return;                 // whitelist enforcement
    root.style.setProperty(name, value);
  }

  function applyAll() {
    Object.keys(overrides).forEach(function (k) { applyOverride(k, overrides[k]); });
  }

  // Apply immediately on load (before the panel is ever opened).
  applyAll();

  // ---- value helpers -----------------------------------------------------
  function format(control, raw) {
    if (control.kind === 'range') return String(raw) + (control.unit || '');
    return String(raw);
  }

  function rgbToHex(str) {
    var m = str.match(/rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)/i);
    if (!m) return null;
    return '#' + [1, 2, 3].map(function (i) {
      return ('0' + parseInt(m[i], 10).toString(16)).slice(-2);
    }).join('');
  }

  // Current effective value of a token (override if set, else computed default).
  function currentRaw(control) {
    if (overrides[control.var] != null) {
      var v = overrides[control.var];
      if (control.kind === 'range') return parseFloat(v);
      return v;
    }
    var computed = getComputedStyle(root).getPropertyValue(control.var).trim();
    if (control.kind === 'range') return parseFloat(computed);
    if (control.kind === 'color') {
      if (/^#/.test(computed)) return computed.length === 4
        ? '#' + computed.slice(1).split('').map(function (c) { return c + c; }).join('')
        : computed;
      var hex = rgbToHex(computed);
      return hex || '#000000';
    }
    // select: match a known option, else fall back to first.
    for (var i = 0; i < control.options.length; i++) {
      if (control.options[i].value === computed) return computed;
    }
    return control.options[0].value;
  }

  // ---- build the GUI -----------------------------------------------------
  function buildPanel() {
    var body = document.getElementById('theme-panel-body');
    if (!body) return;
    body.innerHTML = '';

    THEMEABLE.forEach(function (g) {
      var wrap = document.createElement('div');
      wrap.className = 'ts-group';
      var h = document.createElement('h3');
      h.textContent = g.group;
      wrap.appendChild(h);

      g.controls.forEach(function (control) {
        var box = document.createElement('div');
        box.className = 'ts-control';

        var label = document.createElement('label');
        var text = document.createElement('span');
        text.textContent = control.label;
        label.appendChild(text);

        var raw = currentRaw(control);
        var input;

        if (control.kind === 'range') {
          var valEl = document.createElement('span');
          valEl.className = 'val';
          valEl.textContent = format(control, raw);
          label.appendChild(valEl);

          input = document.createElement('input');
          input.type = 'range';
          input.min = control.min; input.max = control.max; input.step = control.step;
          input.value = raw;
          input.addEventListener('input', function () {
            var v = format(control, input.value);
            valEl.textContent = v;
            overrides[control.var] = input.value;
            applyOverride(control.var, v);
            saveOverrides(overrides);
          });
        } else if (control.kind === 'color') {
          input = document.createElement('input');
          input.type = 'color';
          input.value = raw;
          input.addEventListener('input', function () {
            overrides[control.var] = input.value;
            applyOverride(control.var, input.value);
            saveOverrides(overrides);
          });
        } else { // select
          input = document.createElement('select');
          control.options.forEach(function (opt) {
            var o = document.createElement('option');
            o.value = opt.value; o.textContent = opt.label;
            if (opt.value === raw) o.selected = true;
            input.appendChild(o);
          });
          input.addEventListener('change', function () {
            overrides[control.var] = input.value;
            applyOverride(control.var, input.value);
            saveOverrides(overrides);
          });
        }

        box.appendChild(label);
        box.appendChild(input);
        wrap.appendChild(box);
      });

      body.appendChild(wrap);
    });
  }

  // ---- reset / export / import ------------------------------------------
  function resetAll() {
    Object.keys(overrides).forEach(function (k) { root.style.removeProperty(k); });
    overrides = {};
    saveOverrides(overrides);
    buildPanel();
  }

  function exportTheme() {
    var pkg = {
      name: 'HTMLNote custom theme',
      base: root.dataset.theme || 'light',
      density: root.dataset.density || 'comfortable',
      overrides: overrides
    };
    var blob = new Blob([JSON.stringify(pkg, null, 2)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'htmlnote-theme.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }

  function importTheme(file) {
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var pkg = JSON.parse(reader.result);
        if (pkg.base) {
          localStorage.setItem('htmlnote-theme', pkg.base);
          root.dataset.theme = pkg.base;
        }
        if (pkg.density) {
          localStorage.setItem('htmlnote-density', pkg.density);
          root.dataset.density = pkg.density;
        }
        var next = {};
        var incoming = pkg.overrides || {};
        Object.keys(incoming).forEach(function (k) {
          if (!WHITELIST[k]) return;              // ignore anything off-whitelist
          next[k] = incoming[k];
        });
        // Clear existing, then apply imported.
        Object.keys(overrides).forEach(function (k) { root.style.removeProperty(k); });
        overrides = next;
        applyAll();
        saveOverrides(overrides);
        buildPanel();
      } catch (e) {
        alert('Could not read theme file: ' + e.message);
      }
    };
    reader.readAsText(file);
  }

  // ---- wiring ------------------------------------------------------------
  function openPanel() {
    buildPanel();
    document.getElementById('theme-panel').classList.add('open');
    document.getElementById('theme-backdrop').classList.add('open');
  }
  function closePanel() {
    document.getElementById('theme-panel').classList.remove('open');
    document.getElementById('theme-backdrop').classList.remove('open');
  }

  document.addEventListener('DOMContentLoaded', function () {
    var openBtn = document.getElementById('theme-open');
    var closeBtn = document.getElementById('theme-close');
    var backdrop = document.getElementById('theme-backdrop');
    var resetBtn = document.getElementById('theme-reset');
    var exportBtn = document.getElementById('theme-export');
    var importBtn = document.getElementById('theme-import');
    var importInput = document.getElementById('theme-import-input');

    if (openBtn) openBtn.addEventListener('click', openPanel);
    if (closeBtn) closeBtn.addEventListener('click', closePanel);
    if (backdrop) backdrop.addEventListener('click', closePanel);
    if (resetBtn) resetBtn.addEventListener('click', resetAll);
    if (exportBtn) exportBtn.addEventListener('click', exportTheme);
    if (importBtn) importBtn.addEventListener('click', function () { importInput.click(); });
    if (importInput) importInput.addEventListener('change', function (e) {
      if (e.target.files && e.target.files[0]) importTheme(e.target.files[0]);
      e.target.value = '';
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closePanel();
    });
  });
})();
