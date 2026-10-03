'use strict';
(() => {
  const key = 'orcaprime-theme';
  const choices = [['system', 'Automático'], ['light', 'Claro'], ['dark', 'Escuro']];
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const valid = value => choices.some(([name]) => name === value) ? value : 'system';
  let preference = 'system';
  try { preference = valid(localStorage.getItem(key)); } catch (_) { /* Storage may be disabled. */ }

  function apply() {
    const theme = preference === 'system' ? (system.matches ? 'dark' : 'light') : preference;
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.themePreference = preference;
    document.querySelectorAll('[data-theme-select]').forEach(select => { select.value = preference; });
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = theme === 'dark' ? '#101a29' : '#087dce';
  }

  window.OrcaTheme = {
    control: () => `<label class="theme-picker"><span>Tema</span><select data-theme-select aria-label="Tema">${choices.map(([value, label]) => `<option value="${value}" ${value === preference ? 'selected' : ''}>${label}</option>`).join('')}</select></label>`
  };
  document.addEventListener('change', event => {
    if (!event.target.matches('[data-theme-select]')) return;
    preference = valid(event.target.value);
    try { localStorage.setItem(key, preference); } catch (_) { /* Keep the choice for this page. */ }
    apply();
  });
  system.addEventListener('change', () => { if (preference === 'system') apply(); });
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) { preference = valid(event.newValue); apply(); }
  });
  document.addEventListener('DOMContentLoaded', apply);
  apply();
})();
