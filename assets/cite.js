// Кнопка «Скопировать» в блоке BibTeX на странице статьи (articles/<slug>.html).
// navigator.clipboard есть только в безопасном контексте (https, localhost) —
// при просмотре через file:// или при отказе браузера просто выделяем текст
// записи, чтобы её можно было скопировать вручную.
(function () {
  function selectText(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }

  function flash(btn, label) {
    btn.textContent = label;
    clearTimeout(btn._zhplTimer);
    btn._zhplTimer = setTimeout(function () { btn.textContent = 'Скопировать'; }, 2000);
  }

  window.copyBibtex = function (btn, id) {
    var src = document.getElementById(id);
    if (!src) return;
    var fallback = function () {
      selectText(src);
      flash(btn, 'Выделено — нажмите Ctrl+C');
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(src.textContent).then(
        function () { flash(btn, 'Скопировано'); },
        fallback
      );
    } else {
      fallback();
    }
  };
})();
