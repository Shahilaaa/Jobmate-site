/**
 * JobMate NLP Search — live AI-powered search widget
 * Attaches to any <form data-nlp-search="<page_key>"> containing <input name="q">
 */
(function () {
  'use strict';

  const API_URL = '/api/nlp-search/';
  const DEBOUNCE_MS = 300;
  const MIN_CHARS = 2;

  /* ── Inject CSS ──────────────────────────────────────────────────────────── */
  const style = document.createElement('style');
  style.textContent = `
    /* NLP submit button */
    .nlp-submit-btn {
      background: none;
      border: none;
      padding: 0 12px;
      cursor: pointer;
      font-size: 16px;
      color: #555;
      display: flex;
      align-items: center;
      transition: color 0.15s;
      flex-shrink: 0;
    }
    .nlp-submit-btn:hover { color: #1a73e8; }

    /* AI badge on the input wrapper */
    .nlp-ai-badge {
      position: absolute;
      right: 42px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 9px;
      font-weight: 700;
      letter-spacing: 0.6px;
      color: #1a73e8;
      background: #e8f0fe;
      padding: 2px 6px;
      border-radius: 8px;
      pointer-events: none;
      z-index: 1;
    }

    /* Dropdown */
    .nlp-dropdown {
      display: none;
      position: absolute;
      top: calc(100% + 6px);
      left: 0;
      right: 0;
      background: #fff;
      border: 1px solid #dde3ed;
      border-radius: 10px;
      box-shadow: 0 8px 28px rgba(0,0,0,0.14);
      z-index: 99999;
      max-height: 300px;
      overflow-y: auto;
      animation: nlpFadeIn 0.13s ease;
    }
    @keyframes nlpFadeIn {
      from { opacity: 0; transform: translateY(-6px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .nlp-dropdown-header {
      padding: 7px 14px 5px;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.8px;
      color: #1a73e8;
      text-transform: uppercase;
      border-bottom: 1px solid #f0f0f0;
    }
    .nlp-result-item {
      display: flex;
      flex-direction: column;
      padding: 9px 14px;
      text-decoration: none;
      color: #222;
      border-bottom: 1px solid #f5f5f7;
      transition: background 0.1s;
      cursor: pointer;
    }
    .nlp-result-item:last-child { border-bottom: none; }
    .nlp-result-item:hover,
    .nlp-result-item.nlp-active { background: #f0f4ff; }
    .nlp-label {
      font-size: 13.5px;
      font-weight: 500;
      line-height: 1.4;
    }
    .nlp-label mark {
      background: #fff9c4;
      color: #333;
      border-radius: 2px;
      padding: 0 1px;
      font-style: normal;
    }
    .nlp-sub {
      font-size: 11.5px;
      color: #888;
      margin-top: 1px;
    }
    .nlp-no-results {
      padding: 12px 14px;
      color: #999;
      font-size: 13px;
      font-style: italic;
    }
    .nlp-footer {
      padding: 6px 14px;
      font-size: 10px;
      color: #aaa;
      text-align: right;
      border-top: 1px solid #f0f0f0;
    }

    /* Loading spinner on input */
    .nlp-loading .search-input,
    .nlp-loading input[name="q"] {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='10' fill='none' stroke='%23e0e0e0' stroke-width='3'/%3E%3Cpath d='M12 2a10 10 0 0 1 10 10' fill='none' stroke='%231a73e8' stroke-width='3' stroke-linecap='round'%3E%3CanimateTransform attributeName='transform' type='rotate' from='0 12 12' to='360 12 12' dur='0.8s' repeatCount='indefinite'/%3E%3C/path%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 42px center;
      background-size: 14px;
    }
  `;
  document.head.appendChild(style);

  /* ── Helpers ─────────────────────────────────────────────────────────────── */
  function debounce(fn, ms) {
    let t;
    return function (...args) { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), ms); };
  }

  function escHtml(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function highlight(text, query) {
    const tokens = query.replace(/[^a-z0-9 ]/gi, ' ').trim().split(/\s+/).filter(t => t.length >= 2);
    tokens.forEach(tok => {
      const re = new RegExp('(' + tok.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
      text = text.replace(re, '<mark>$1</mark>');
    });
    return text;
  }

  /* ── Per-form initialisation ─────────────────────────────────────────────── */
  function initForm(form) {
    const pageKey = form.dataset.nlpSearch;
    if (!pageKey) return;
    const input = form.querySelector('input[name="q"]');
    if (!input) return;

    // Add AI badge
    const badge = document.createElement('span');
    badge.className = 'nlp-ai-badge';
    badge.textContent = 'AI';
    form.appendChild(badge);

    // Create dropdown
    const dropdown = document.createElement('div');
    dropdown.className = 'nlp-dropdown';
    dropdown.setAttribute('role', 'listbox');
    form.appendChild(dropdown);

    let activeIdx = -1;

    function setLoading(on) {
      form.classList.toggle('nlp-loading', on);
    }

    function closeDropdown() {
      dropdown.style.display = 'none';
      activeIdx = -1;
    }

    function renderResults(results, query) {
      dropdown.innerHTML = '';
      if (!results || !results.length) {
        dropdown.innerHTML = `<div class="nlp-no-results">No results for "<strong>${escHtml(query)}</strong>"</div>`;
        dropdown.style.display = 'block';
        return;
      }
      const header = document.createElement('div');
      header.className = 'nlp-dropdown-header';
      header.textContent = `AI Search — ${results.length} result${results.length !== 1 ? 's' : ''}`;
      dropdown.appendChild(header);

      results.forEach(r => {
        const a = document.createElement('a');
        a.className = 'nlp-result-item';
        a.href = r.url || '#';
        a.setAttribute('role', 'option');
        a.setAttribute('tabindex', '0');
        a.innerHTML = `<span class="nlp-label">${highlight(escHtml(r.label), query)}</span>` +
                      (r.sub ? `<span class="nlp-sub">${escHtml(r.sub)}</span>` : '');
        dropdown.appendChild(a);
      });

      const footer = document.createElement('div');
      footer.className = 'nlp-footer';
      footer.textContent = '↵ Press Enter to see all results';
      dropdown.appendChild(footer);

      dropdown.style.display = 'block';
      activeIdx = -1;
    }

    const doSearch = debounce(async function(query) {
      if (query.length < MIN_CHARS) { closeDropdown(); return; }

      setLoading(true);
      try {
        const url = `${API_URL}?page=${encodeURIComponent(pageKey)}&q=${encodeURIComponent(query)}`;
        const res = await fetch(url, {
          credentials: 'same-origin',
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });

        // If server returns non-JSON (e.g. login redirect), silently ignore
        const ct = res.headers.get('content-type') || '';
        if (!ct.includes('json')) { closeDropdown(); return; }

        const data = await res.json();
        if (data.results !== undefined) {
          renderResults(data.results, query);
        }
      } catch (e) {
        closeDropdown();
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);

    input.addEventListener('input', () => doSearch(input.value.trim()));

    input.addEventListener('focus', () => {
      if (input.value.trim().length >= MIN_CHARS && dropdown.children.length > 0) {
        dropdown.style.display = 'block';
      }
    });

    // Keyboard navigation
    input.addEventListener('keydown', e => {
      const items = dropdown.querySelectorAll('.nlp-result-item');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        activeIdx = Math.min(activeIdx + 1, items.length - 1);
        items.forEach((el, i) => el.classList.toggle('nlp-active', i === activeIdx));
        if (items[activeIdx]) items[activeIdx].scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        activeIdx = Math.max(activeIdx - 1, -1);
        items.forEach((el, i) => el.classList.toggle('nlp-active', i === activeIdx));
      } else if (e.key === 'Enter' && activeIdx >= 0 && items[activeIdx]) {
        e.preventDefault();
        items[activeIdx].click();
      } else if (e.key === 'Escape') {
        closeDropdown();
      }
    });

    // Close on outside click
    document.addEventListener('click', e => {
      if (!form.contains(e.target)) closeDropdown();
    });
  }

  /* ── Boot ────────────────────────────────────────────────────────────────── */
  function init() {
    document.querySelectorAll('form[data-nlp-search]').forEach(initForm);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
