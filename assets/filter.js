// Клиентский фильтр тизеров статей на главной по ключевому слову. Не трогает
// ничего на сервере: каждая карточка <article class="article"> в #issue несёт
// data-keywords="тег1|тег2|..." (см. render_teaser в scripts/gen_site.py),
// а каждый её тег — кликабельная кнопка .kw. Клик по тегу показывает только
// карточки, содержащие этот тег; повторный клик по тому же тегу снимает
// фильтр. Загружается только на index.html (страницы статей фильтровать
// нечего — там теги статичны).
(function () {
  var active = null;

  function keywordsOf(article) {
    return (article.getAttribute('data-keywords') || '').split('|').filter(Boolean);
  }

  function applyFilter(kw) {
    var articles = document.querySelectorAll('#issue .article');
    var shown = 0;
    for (var i = 0; i < articles.length; i++) {
      var a = articles[i];
      var show = !kw || keywordsOf(a).indexOf(kw) !== -1;
      a.hidden = !show;
      if (show) shown++;
    }

    var chips = document.querySelectorAll('#issue .kw');
    for (var j = 0; j < chips.length; j++) {
      chips[j].setAttribute('aria-pressed', chips[j].textContent === kw ? 'true' : 'false');
    }

    var status = document.getElementById('kw-filter-status');
    if (status) {
      status.hidden = !kw;
      if (kw) {
        status.querySelector('.kw-filter-term').textContent = kw;
        status.querySelector('.kw-filter-count').textContent = shown;
      }
    }
  }

  window.toggleKeywordFilter = function (el) {
    var kw = el.textContent;
    active = active === kw ? null : kw;
    applyFilter(active);
  };

  window.clearKeywordFilter = function () {
    active = null;
    applyFilter(null);
  };
})();
