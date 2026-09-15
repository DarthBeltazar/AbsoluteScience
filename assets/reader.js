// Логика встроенной PDF-читалки статьи: переключатель «Читать на сайте» и
// светлый/тёмный вариант PDF внутри неё. Общий файл для всех страниц
// articles/<slug>.html — раньше это был инлайн-скрипт в index.html, но с
// переездом полного текста статей на отдельные страницы (gen_site.py) его
// пришлось бы дублировать в каждой из них. Требует assets/theme.js,
// подключённый раньше этого файла (используется window.ZhplTheme).
(function () {
  // Переключение темы сайта живёт в assets/theme.js (общее с index.html/404.html);
  // здесь используем его через window.ZhplTheme, чтобы PDF-читалка могла
  // по умолчанию следовать теме сайта.
  var siteIsDark = window.ZhplTheme.siteIsDark;

  var prevToggleTheme = window.toggleTheme;
  window.toggleTheme = function () {
    prevToggleTheme();
    // PDF-читалка без собственного явного выбора продолжает следовать теме сайта.
    if (stored() === null) applyPdfDark(pdfDarkOn());
  };

  var KEY = 'zhpl:pdfDark';

  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function store(v) {
    try { localStorage.setItem(KEY, v); } catch (e) {}
  }
  // По умолчанию следуем теме сайта; явный выбор пользователя её перекрывает.
  function pdfDarkOn() {
    var s = stored();
    return s === null ? siteIsDark() : s === '1';
  }
  // У статьи есть два PDF: обычный (data-src) и тёмный (data-dark-src).
  function readerSrc(frame, on) {
    return on ? frame.getAttribute('data-dark-src') : frame.getAttribute('data-src');
  }
  function applyPdfDark(on) {
    var frames = document.querySelectorAll('.pdf-reader');
    for (var i = 0; i < frames.length; i++) {
      var f = frames[i];
      var want = readerSrc(f, on);
      if (f.getAttribute('src') && f.getAttribute('src') !== want) {
        f.setAttribute('src', want);            // читалка уже открыта — перегружаем нужный вариант
      }
      var wrap = f.closest ? f.closest('.pdf-reader-wrap') : null;
      var link = wrap && wrap.querySelector('.pdf-reader-link');
      if (link) link.setAttribute('href', want);
    }
    var btns = document.querySelectorAll('.pdf-dark-btn');
    for (var j = 0; j < btns.length; j++) {
      btns[j].textContent = on ? 'Обычный PDF' : 'Тёмный PDF';
      btns[j].setAttribute('aria-pressed', on ? 'true' : 'false');
    }
  }

  window.togglePdfDark = function () {
    var on = !pdfDarkOn();
    store(on ? '1' : '0');
    applyPdfDark(on);
  };

  window.toggleReader = function (btn, id) {
    var wrap = document.getElementById(id + '-wrap');
    var frame = document.getElementById(id);
    var opening = wrap.hasAttribute('hidden');
    if (opening) {
      if (!frame.getAttribute('src')) {
        frame.setAttribute('src', readerSrc(frame, pdfDarkOn()));
      }
      applyPdfDark(pdfDarkOn());
      wrap.hidden = false;
      btn.textContent = 'Свернуть статью';
      btn.setAttribute('aria-expanded', 'true');
      wrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
      wrap.hidden = true;
      btn.textContent = 'Читать на сайте';
      btn.setAttribute('aria-expanded', 'false');
    }
  };

  // Синхронизируем подписи кнопок читалки с текущим режимом сразу при загрузке
  // (тему самой страницы theme.js уже применил).
  applyPdfDark(pdfDarkOn());

  // Пока пользователь не выбрал тему явно — PDF следует за сменой системной темы.
  if (window.matchMedia) {
    try {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
        if (window.ZhplTheme.storedTheme() === null && stored() === null) applyPdfDark(pdfDarkOn());
      });
    } catch (e) {}
  }
})();
