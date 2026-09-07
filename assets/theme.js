// Общая логика ручного переключения темы (кнопка в шапке) — используется и на
// index.html, и на 404.html. Не отвечает за тёмный PDF в читалке статьи: та
// логика — в inline-скрипте index.html, она обращается сюда через window.ZhplTheme.
(function () {
  var THEME_KEY = 'zhpl:theme';

  function storedTheme() {
    try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; }
  }
  function storeTheme(v) {
    try { localStorage.setItem(THEME_KEY, v); } catch (e) {}
  }
  function systemPrefersDark() {
    return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  }
  // Тема сайта: явный выбор пользователя (кнопка в шапке) перекрывает системную.
  function siteIsDark() {
    var t = storedTheme();
    return t === null ? systemPrefersDark() : t === 'dark';
  }
  function applyTheme() {
    var dark = siteIsDark();
    var explicit = storedTheme() !== null;
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');

    var btn = document.getElementById('theme-toggle-btn');
    if (btn) {
      btn.textContent = dark ? '☀️ Светлая тема' : '🌙 Тёмная тема';
      btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
    }
    var meta = document.getElementById('theme-color-meta');
    if (meta) meta.setAttribute('content', dark ? '#1c1a15' : '#faf6ee');

    // При явном выборе темы фавикон и герб в шапке перестают зависеть от
    // системной настройки — иначе они рассинхронизируются с остальной страницей.
    var favLight = document.getElementById('favicon-light');
    var favDark = document.getElementById('favicon-dark');
    if (favLight && favDark) {
      favLight.media = explicit ? (dark ? 'not all' : 'all') : '(prefers-color-scheme: light)';
      favDark.media = explicit ? (dark ? 'all' : 'not all') : '(prefers-color-scheme: dark)';
    }
    var sealDark = document.getElementById('seal-dark-source');
    if (sealDark) sealDark.media = explicit ? (dark ? 'all' : 'not all') : '(prefers-color-scheme: dark)';
  }

  window.toggleTheme = function () {
    storeTheme(siteIsDark() ? 'light' : 'dark');
    applyTheme();
  };

  // Публичный доступ для index.html — там читалка PDF по умолчанию следует теме сайта.
  window.ZhplTheme = { siteIsDark: siteIsDark, storedTheme: storedTheme, applyTheme: applyTheme };

  applyTheme();

  // Пока пользователь не выбрал тему явно — реагируем на смену системной темы.
  if (window.matchMedia) {
    try {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
        if (storedTheme() === null) applyTheme();
      });
    } catch (e) {}
  }
})();
