/*
 * visi-profile.js — the ".visi key" personal session module.
 *
 * A small portable JSON key stored in localStorage['fshs_visi_key'] that
 * remembers the visitor's watch criteria (profile) AND the recalls/news
 * they choose to keep (saved_items). No account, no network requests.
 *
 * Exposes (window level, consumed by index.html):
 *   VISI_PROFILE   — the full key object, or null when no key exists
 *   VISI_SAVED     — live array of saved items ({type:'recall'|'news', ...})
 *   VISI_SOURCES   — live array of favorite source names (sources.favorites)
 *   VisiProfile    — { open, save, download, reset, importFile,
 *                      removeSavedItem, toggleSaved, refreshCounter,
 *                      hasKey, close }
 *   document event 'visi-profile-updated' fired on every state change.
 *
 * Strings come from the main page's I18N table (window.t), so the module
 * must only render text after the main script has run. Init is deferred to
 * DOMContentLoaded for that reason; only _load() (no DOM, no i18n) runs at
 * script-load time so index.html's early data callbacks can read the key.
 */
(function () {
  'use strict';
  var LS_KEY = 'fshs_visi_key';
  var LS_BANNER = 'fshs_visi_banner';
  var profile = null;
  var pendingItem = null;

  function _t(key) {
    try { if (typeof window.t === 'function') return window.t(key); } catch (e) {}
    return key;
  }

  /* ---- state ---------------------------------------------------------- */

  function _ensure(p) {
    p.version = p.version || '1.1';
    p.profile = p.profile || {};
    var pr = p.profile;
    pr.product_types = Array.isArray(pr.product_types) ? pr.product_types : [];
    pr.hazards = Array.isArray(pr.hazards) ? pr.hazards : [];
    pr.regions = Array.isArray(pr.regions) ? pr.regions : [];
    pr.countries = Array.isArray(pr.countries) ? pr.countries : [];
    if (pr.min_tier !== 'tier1' && pr.min_tier !== 'tier2') pr.min_tier = 'all';
    p.sources = p.sources || {};
    p.sources.favorites = Array.isArray(p.sources.favorites) ? p.sources.favorites : [];
    p.saved_items = Array.isArray(p.saved_items) ? p.saved_items : [];
    p.preferences = p.preferences || {};
    p.created_at = p.created_at || new Date().toISOString();
    p.updated_at = p.updated_at || new Date().toISOString();
    return p;
  }

  function _load() {
    var raw = null;
    try { raw = localStorage.getItem(LS_KEY); } catch (e) {}
    profile = null;
    window.VISI_PROFILE = null;
    window.VISI_SAVED = [];
    window.VISI_SOURCES = [];
    if (raw) {
      try {
        var k = JSON.parse(raw);
        if (k && typeof k === 'object' && k.version) {
          profile = _ensure(k);
          window.VISI_PROFILE = profile;
          window.VISI_SAVED = profile.saved_items;
          window.VISI_SOURCES = profile.sources.favorites;
        }
      } catch (e) { profile = null; }
    }
  }

  function _safeUrl(u) {
    var s = String(u == null ? '' : u).trim();
    return /^https?:\/\/\S+/i.test(s) ? s : '';
  }

  function _broadcast(scope) {
    refreshCounter();
    hideBanner();
    try {
      document.dispatchEvent(new CustomEvent('visi-profile-updated', {
        detail: { scope: scope || 'all' }
      }));
    } catch (e) {}
  }

  // scope distinguishes why the key changed:
  //   'all'       — watch criteria / sources changed (must re-filter the table)
  //   'favorites' — only a saved item was added/removed (just refresh icons)
  function _persist(scope) {
    if (!profile) return;
    profile.updated_at = new Date().toISOString();
    try { localStorage.setItem(LS_KEY, JSON.stringify(profile)); } catch (e) {}
    try { localStorage.setItem(LS_BANNER, 'created'); } catch (e) {}
    window.VISI_PROFILE = profile;
    window.VISI_SAVED = profile.saved_items;
    window.VISI_SOURCES = profile.sources.favorites;
    _broadcast(scope);
  }

  function hasKey() { return !!profile; }

  /* ---- saved items ---------------------------------------------------- */

  function toggleSaved(item) {
    if (!profile) {
      pendingItem = item;
      openModal({ pending: true });
      return;
    }
    var list = profile.saved_items;
    var i = -1;
    for (var x = 0; x < list.length; x++) {
      if (list[x].type === item.type && list[x].id === item.id) { i = x; break; }
    }
    if (i >= 0) {
      list.splice(i, 1);
    } else {
      var entry = {
        type: item.type || 'recall',
        id: item.id,
        title: item.title || '',
        source: item.source || '',
        date: item.date || '',
        link: item.link || '',
        saved_at: new Date().toISOString()
      };
      if (item.type === 'news') entry.category = item.category || 'outbreak';
      else entry['class'] = 'Recall';
      list.push(entry);
    }
    _persist('favorites');
  }

  function removeSavedItem(type, id) {
    if (!profile) return;
    profile.saved_items = profile.saved_items.filter(function (it) {
      return !(it.type === type && it.id === id);
    });
    _persist('favorites');
    _renderModal();
  }

  /* ---- banner --------------------------------------------------------- */

  function _dismissBanner() {
    try { localStorage.setItem(LS_BANNER, 'seen'); } catch (e) {}
    hideBanner();
  }
  function hideBanner() {
    var b = document.getElementById('visiBanner');
    if (b) b.style.display = 'none';
  }
  function _maybeShowBanner() {
    var banner = document.getElementById('visiBanner');
    if (!banner) return;
    var flag = null; try { flag = localStorage.getItem(LS_BANNER); } catch (e) {}
    banner.style.display = (!profile && !flag) ? 'flex' : 'none';
  }

  /* ---- modal ---------------------------------------------------------- */

  function openModal(opts) {
    opts = opts || {};
    if (!opts.pending) pendingItem = null;
    var ov = document.getElementById('visiModal');
    if (!ov) return;
    ov.style.display = 'flex';
    _dismissBanner();
    _renderModal();
  }

  function closeModal() {
    var ov = document.getElementById('visiModal');
    if (ov) ov.style.display = 'none';
  }

  function _optValues(id) {
    var el = document.getElementById(id);
    if (!el || !el.options) return [];
    var out = [];
    for (var i = 0; i < el.options.length; i++) {
      var o = el.options[i];
      if (o && o.value) out.push({ v: o.value, l: o.textContent });
    }
    return out;
  }

  function _esc(s) { return String(s == null ? '' : s).replace(/</g, '&lt;').replace(/"/g, '&quot;'); }
  function _escSq(s) { return String(s == null ? '' : s).replace(/</g, '&lt;').replace(/'/g, '&#39;').replace(/"/g, '&quot;'); }

  function _groupHtml(name, label, opts, sel) {
    var h = '<div class="visi-crit"><label class="visi-glabel">' + label + '</label>';
    if (!opts.length) { h += '<div class="visi-empty">…</div></div>'; return h; }
    h += '<div class="visi-chklist">';
    for (var i = 0; i < opts.length; i++) {
      var o = opts[i];
      var on = sel.indexOf(o.v) !== -1;
      h += '<label class="visi-chk"><input type="checkbox" name="' + name + '" value="' + _esc(o.v) + '"' + (on ? ' checked' : '') + '><span>' + _esc(o.l) + '</span></label>';
    }
    return h + '</div></div>';
  }

  function _radio(v, lbl, cur) {
    return '<label class="visi-chk"><input type="radio" name="visiMinTier" value="' + v + '"' + (cur === v ? ' checked' : '') + '><span>' + lbl + '</span></label>';
  }

  function _savedHtml(items) {
    var sorted = items.slice().sort(function (a, b) {
      return String(b.date || b.saved_at || '').localeCompare(String(a.date || a.saved_at || ''));
    });
    var h = '<div class="visi-savedlist">';
    for (var i = 0; i < sorted.length; i++) {
      var it = sorted[i];
      var tag = it.type === 'news'
        ? '<span class="visi-tag news">' + _esc(it.category || 'news') + '</span>'
        : '<span class="visi-tag recall">Rappel</span>';
      var safeLink = _safeUrl(it.link);
      var link = safeLink
        ? '<a href="' + _esc(safeLink) + '" target="_blank" rel="noopener" title="' + _esc(it.title) + '">' + _esc(it.title || '—') + '</a>'
        : '<span title="' + _esc(it.title) + '">' + _esc(it.title || '—') + '</span>';
      var meta = (it.date || it.saved_at || '').slice(0, 10);
      h += '<div class="visi-saved-item">' + tag + link +
        '<span class="visi-saved-date">' + meta + '</span>' +
        '<button type="button" class="visi-rm" onclick="VisiProfile.removeSavedItem(\'' + it.type + '\',\'' + _escSq(it.id) + '\')" aria-label="Remove">✕</button></div>';
    }
    return h + '</div>';
  }

  function _renderModal() {
    var body = document.getElementById('visiBody');
    if (!body) return;
    var p = profile;
    var grouped = {
      product: _optValues('prodf'),
      hazards: _optValues('pathf'),
      sources: _optValues('srcf'),
      countries: _optValues('ctryf'),
      regions: _optValues('regf')
    };
    var savedCount = p ? p.saved_items.length : 0;
    body.innerHTML =
      '<div class="visi-note"><b>🔒 ' + _t('navVisiKey') + '</b> — ' + _t('visiIntro') + '</div>' +
      '<div class="visi-group"><div class="sec">' + _t('visiSectionProfile') + '</div>' +
      _groupHtml('visiCkProd', _t('fbProduct'), grouped.product, p ? p.profile.product_types : []) +
      _groupHtml('visiCkHaz', _t('fbPathogen'), grouped.hazards, p ? p.profile.hazards : []) +
      _groupHtml('visiCkSrc', _t('visiGroupSources'), grouped.sources, p ? p.sources.favorites : []) +
      _groupHtml('visiCkCtr', _t('fbCountry'), grouped.countries, p ? p.profile.countries : []) +
      _groupHtml('visiCkReg', _t('fbRegion'), grouped.regions, p ? p.profile.regions : []) +
      '<div class="visi-crit"><label class="visi-glabel">' + _t('visiGroupTier') + '</label>' +
      '<div class="visi-minrow">' +
      _radio('all', _t('visiMinAll'), p ? p.profile.min_tier : 'all') +
      _radio('tier2', _t('visiMinTier2'), p ? p.profile.min_tier : 'all') +
      _radio('tier1', _t('visiMinTier1'), p ? p.profile.min_tier : 'all') +
      '</div></div></div>' +
      '<div class="visi-group"><div class="sec">' + _t('visiSectionSaved') + ' <span class="visi-num">(' + savedCount + ')</span></div>' +
      (savedCount ? _savedHtml(p.saved_items) : '<div class="visi-empty">' + _t('visiSavedClean') + '</div>') +
      '</div>' +
      '<div id="visiMsg"></div>' +
      '<div class="visi-actions">' +
      '<button type="button" class="pb on" onclick="VisiProfile.save()">🔒 ' + (p ? _t('visiUpdate') : _t('visiSave')) + '</button>' +
      '<button type="button" class="pb" onclick="VisiProfile.download()">' + _t('visiDownload') + '</button>' +
      '<label class="pb visi-filebtn">' + _t('visiImport') + '<input type="file" accept="application/json,.json" onchange="VisiProfile.importFile(this)"></label>' +
      '<button type="button" class="pb visi-danger" onclick="VisiProfile.reset()">' + _t('visiReset') + '</button>' +
      '</div>';
  }

  function showMsg(kind, text) {
    var m = document.getElementById('visiMsg');
    if (!m) return;
    m.className = kind === 'err' ? 'visi-err' : 'visi-ok';
    m.textContent = text;
  }

  /* ---- actions -------------------------------------------------------- */

  function save() {
    if (!profile) profile = _ensure({ version: '1.1' });
    function sel(name) {
      var out = [];
      var els = document.querySelectorAll('input[name="' + name + '"]:checked');
      for (var i = 0; i < els.length; i++) out.push(els[i].value);
      return out;
    }
    var pr = profile.profile;
    pr.product_types = sel('visiCkProd');
    pr.hazards = sel('visiCkHaz');
    pr.countries = sel('visiCkCtr');
    pr.regions = sel('visiCkReg');
    profile.sources = profile.sources || {};
    profile.sources.favorites = sel('visiCkSrc');
    var mt = document.querySelector('input[name="visiMinTier"]:checked');
    pr.min_tier = mt ? mt.value : 'all';
    profile.preferences = profile.preferences || {};
    var lng = 'en'; try { lng = localStorage.getItem('fshs_lang') || 'en'; } catch (e) {}
    profile.preferences.language = lng === 'fr' ? 'FR' : 'EN';
    profile.updated_at = new Date().toISOString();
    if (pendingItem) {
      var it = pendingItem; pendingItem = null;
      var entry = {
        type: it.type || 'recall', id: it.id, title: it.title || '',
        source: it.source || '', date: it.date || '', link: it.link || '',
        saved_at: new Date().toISOString()
      };
      if (it.type === 'news') entry.category = it.category || 'outbreak';
      else entry['class'] = 'Recall';
      profile.saved_items.push(entry);
    }
    _persist('all');
    _renderModal();
    showMsg('ok', _t('visiSaveOk'));
  }

  function download() {
    if (!profile) return;
    var blob = new Blob([JSON.stringify(profile, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = 'visi-key.json';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function importFile(input) {
    var f = input && input.files && input.files[0];
    if (!f) return;
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var k = JSON.parse(String(reader.result));
        if (!k || typeof k !== 'object' || !k.version ||
            !k.profile || typeof k.profile !== 'object') throw new Error('bad-key');
        // Never trust links inside an imported/shared key: drop everything
        // that isn't a plain http(s) URL so a malicious key can't inject JS.
        if (Array.isArray(k.saved_items)) {
          k.saved_items.forEach(function (it) {
            if (it && it.link && !_safeUrl(it.link)) it.link = '';
          });
        }
        profile = _ensure(k);
        pendingItem = null;
        _persist('all');
        _renderModal();
        showMsg('ok', _t('visiImportOk'));
      } catch (err) {
        _renderModal();
        showMsg('err', _t('visiImportInvalid'));
      }
    };
    reader.readAsText(f);
    if (input) input.value = '';
  }

  function reset() {
    if (!confirm(_t('visiResetConfirm'))) return;
    try { localStorage.removeItem(LS_KEY); } catch (e) {}
    // Restore the "first visit" state: without a key AND without the banner
    // flag, the "Créer ma clé / Continuer sans clé" banner shows again.
    try { localStorage.removeItem(LS_BANNER); } catch (e) {}
    pendingItem = null;
    _load();
    refreshCounter();
    var ov = document.getElementById('visiModal');
    if (ov && ov.style.display === 'flex') _renderModal();
    _broadcast('all');
    _maybeShowBanner();
  }

  /* ---- counter -------------------------------------------------------- */

  function _countCriteria() {
    if (!profile) return 0;
    var pr = profile.profile || {};
    var n = 0;
    if (pr.product_types && pr.product_types.length) n++;
    if (pr.hazards && pr.hazards.length) n++;
    if (pr.countries && pr.countries.length) n++;
    if (pr.regions && pr.regions.length) n++;
    if (pr.min_tier && pr.min_tier !== 'all') n++;
    return n;
  }

  function refreshCounter() {
    var c = document.getElementById('visiCounter');
    if (!c) return;
    if (!profile) {
      c.style.display = 'none';
      c.textContent = '';
      return;
    }
    c.style.display = 'inline';
    c.textContent = ' · ' + _t('visiCriteriaCount').replace('{n}', _countCriteria()) +
      ' · ' + _t('visiSavedCount').replace('{n}', profile.saved_items.length);
  }

  function refresh() {
    refreshCounter();
    var ov = document.getElementById('visiModal');
    if (ov && ov.style.display === 'flex') _renderModal();
  }

  /* ---- init ----------------------------------------------------------- */

  function init() {
    _load();
    refreshCounter();
    _maybeShowBanner();
    var bc = document.getElementById('visiBannerCreate');
    if (bc) bc.addEventListener('click', function () { _dismissBanner(); openModal(); });
    var bl = document.getElementById('visiBannerLater');
    if (bl) bl.addEventListener('click', function () { _dismissBanner(); });
    var cx = document.getElementById('visiClose');
    if (cx) cx.addEventListener('click', closeModal);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });
    document.addEventListener('click', function (e) {
      if (e.target && e.target.id === 'visiModal') closeModal();
    });
  }

  _load(); // read key immediately so index.html data callbacks see it even
           // before DOMContentLoaded, before the main inline script runs.

  window.VisiProfile = {
    open: openModal, close: closeModal, save: save, download: download,
    reset: reset, importFile: importFile, removeSavedItem: removeSavedItem,
    toggleSaved: toggleSaved, refreshCounter: refreshCounter, refresh: refresh,
    hasKey: hasKey
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();