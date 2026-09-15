#!/usr/bin/env python3
"""Пересобрать блок «Текущий номер», счётчики в index.html, страницы отдельных
статей и sitemap.xml из articles/articles.json.

articles.json — единственный источник правды по метаданным статей и авторов.
Сайт их больше не хранит вручную. Статья с "hidden": true пропускается: не
попадает в тизеры на главной, в счётчик и в sitemap.xml, но её .tex/.pdf/.html
остаются в репозитории и доступны по прямой ссылке (страница помечается
noindex). В index.html скрипт трогает только области между маркерами:

    <!-- ARTICLES:START --> ... <!-- ARTICLES:END -->     — тизеры статей
    <!-- STAT:articles --> ... <!-- /STAT:articles -->     — число опубликованных статей
    <!-- STAT:volume --> ... <!-- /STAT:volume -->         — номер тома
    <!-- ISSUE-HEADING --> ... <!-- /ISSUE-HEADING -->     — «Том N · YYYY»
    <!-- STAT:person:<id> --> ... <!-- /STAT:person:<id> --> — число статей автора
                                                               (карточки #people;
                                                               id берётся из
                                                               articles.json → people)

Каждой статье (включая скрытые) генерируется полноценная страница
articles/<slug>.html с полным текстом, вложенной PDF-читалкой и своими
og:title/og:description — она перезаписывается целиком, как и sitemap.xml.
Остальная разметка index.html не изменяется.

Использование:
    python scripts/gen_site.py            # переписать index.html, articles/*.html и sitemap.xml
    python scripts/gen_site.py --check    # не писать; код возврата 1, если файлы устарели
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "articles" / "articles.json"
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
ARTICLES_DIR = ROOT / "articles"
BASE_URL = "https://darthbeltazar.github.io/AbsoluteScience/"


def short_title(title_html: str) -> str:
    """Часть заголовка до двоеточия, без тегов — для <title>, og:title и т.п."""
    text = re.sub(r"<[^>]+>", " ", title_html)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.split(":", 1)[0].strip()


def plain_text(fragment: str) -> str:
    """HTML-фрагмент (аннотация и т.п.) → чистый текст с раскрытыми сущностями."""
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, limit: int = 200) -> str:
    """Обрезать по границе слова и добавить «…» — для meta description."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",.;:—-")
    return cut + "…"


def ru_count(n: int, one: str, few: str, many: str) -> str:
    """Русское склонение существительного после числительного n (1 статья,
    2 статьи, 5 статей, 11 статей, 21 статья, ...)."""
    n_mod100 = n % 100
    n_mod10 = n % 10
    if 11 <= n_mod100 <= 14:
        return many
    if n_mod10 == 1:
        return one
    if 2 <= n_mod10 <= 4:
        return few
    return many


def visible_articles(manifest: dict) -> list[dict]:
    """Статьи с "hidden": true пропускаются — файлы (.tex/.pdf/.html) остаются в
    репозитории и доступны по прямой ссылке, но не показываются на сайте и
    не входят в счётчик "ОПУБЛИКОВАННЫЕ СТАТЬИ". Для черновиков/статей,
    временно снятых с публикации."""
    return [a for a in manifest["articles"] if not a.get("hidden")]


# ---------- Тизер статьи на главной ----------

def render_teaser(art: dict) -> str:
    """Краткая карточка статьи для «Текущего номера» — полный текст, аннотация
    и читалка живут на отдельной странице статьи (см. render_article_page)."""
    kicker = html.escape(art["kicker"])
    title_html = art["titleHtml"]  # намеренно содержит <br>, вставляется как есть
    authors = html.escape(art["authors"])
    art_id = art["id"]
    page = f"articles/{art_id}.html"
    pdf = f"articles/{art_id}.pdf"

    highlights = "\n".join(
        f"          <li>{h}</li>" for h in art["highlights"]  # <em>/<sub> допускаются
    )
    keywords = "".join(
        f'<span class="kw">{html.escape(k)}</span>' for k in art["keywords"]
    )

    return f"""      <article class="article">
        <p class="article-kicker">{kicker}</p>
        <h3><a href="{page}">{title_html}</a></h3>
        <p class="authors">{authors}</p>

        <ul class="highlights">
{highlights}
        </ul>

        <p class="keywords">
          {keywords}
        </p>

        <div class="article-actions">
          <a class="btn primary" href="{page}">Читать статью →</a>
          <a class="btn secondary" href="{pdf}">Скачать PDF</a>
        </div>
      </article>"""


def render_articles(manifest: dict) -> str:
    blocks = [render_teaser(art) for art in visible_articles(manifest)]
    return "\n\n".join(blocks)


# ---------- Полный текст статьи (используется только на её отдельной странице) ----------

def render_article_body(art: dict) -> str:
    """Полная карточка статьи: аннотация, highlights, ключевые слова, cite-box,
    кнопки и встроенная PDF-читалка. Пути — относительно articles/<slug>.html,
    т.е. без префикса "articles/"."""
    kicker = html.escape(art["kicker"])
    title_html = art["titleHtml"]
    authors = html.escape(art["authors"])
    abstract = html.escape(art["abstract"])
    cite_html = art["citeHtml"]    # содержит <em>, как есть
    doi = html.escape(art["doi"])
    art_id = art["id"]
    pdf = f"{art_id}.pdf"
    tex = f"{art_id}.tex"
    short = short_title(title_html)
    reader_name = html.escape(short)
    iframe_title = html.escape(f"{short} — полный текст")
    pdf_view = f"{pdf}#view=FitH"  # открывать по ширине страницы
    pdf_dark_view = f"{art_id}.dark.pdf#view=FitH"  # тёмный вариант

    highlights = "\n".join(
        f"          <li>{h}</li>" for h in art["highlights"]
    )
    keywords = "".join(
        f'<span class="kw">{html.escape(k)}</span>' for k in art["keywords"]
    )

    return f"""      <article class="article">
        <p class="article-kicker">{kicker}</p>
        <h3>{title_html}</h3>
        <p class="authors">{authors}</p>

        <span class="abstract-label">Аннотация</span>
        <p class="abstract">
          {abstract}
        </p>

        <ul class="highlights">
{highlights}
        </ul>

        <p class="keywords">
          {keywords}
        </p>

        <div class="cite-box">
          Как цитировать: {cite_html}
          <span class="doi">DOI: {doi}</span>
        </div>

        <div class="article-actions">
          <button type="button" class="btn read-btn" aria-expanded="false" onclick="toggleReader(this, 'reader')">Читать на сайте</button>
          <a class="btn secondary" href="{pdf}">Скачать PDF</a>
          <a class="btn secondary" href="{tex}">Исходник (.tex)</a>
        </div>

        <div class="pdf-reader-wrap" id="reader-wrap" hidden>
          <div class="pdf-reader-bar">
            <span class="pdf-reader-name">{reader_name}</span>
            <button type="button" class="pdf-dark-btn" aria-pressed="false" onclick="togglePdfDark()">Тёмный PDF</button>
            <a class="pdf-reader-link" href="{pdf_view}" target="_blank" rel="noopener">Открыть отдельно ↗</a>
          </div>
          <iframe id="reader" class="pdf-reader"
                  data-src="{pdf_view}" data-dark-src="{pdf_dark_view}"
                  title="{iframe_title}"></iframe>
        </div>
      </article>"""


def render_article_page(art: dict) -> str:
    """Полная HTML-страница articles/<slug>.html: та же шапка/подвал, что на
    главной, плюс полный текст одной статьи. Генерируется и для скрытых
    статей (noindex), чтобы прямая ссылка продолжала работать."""
    short = short_title(art["titleHtml"])
    page_title = html.escape(f"{short} — Журнал Прикладной Лженауки")
    description = html.escape(truncate(plain_text(art["abstract"])))
    canonical = f"{BASE_URL}articles/{art['id']}.html"
    robots = (
        '\n<meta name="robots" content="noindex">' if art.get("hidden") else ""
    )
    body = render_article_body(art)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title}</title>{robots}
<meta name="description" content="{description}">

<meta property="og:type" content="article">
<meta property="og:site_name" content="Журнал Прикладной Лженауки">
<meta property="og:title" content="{html.escape(short)}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="ru_RU">
<meta property="og:image" content="{BASE_URL}assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(short)}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{BASE_URL}assets/og-image.png">
<link rel="canonical" href="{canonical}">

<meta name="theme-color" content="#faf6ee" id="theme-color-meta">

<link rel="stylesheet" href="../assets/style.css">
<link rel="icon" href="../favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="../assets/logo-mark.svg" media="(prefers-color-scheme: light)" id="favicon-light">
<link rel="icon" type="image/svg+xml" href="../assets/logo-mark-dark.svg" media="(prefers-color-scheme: dark)" id="favicon-dark">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<script>
// Применяем сохранённый выбор темы до отрисовки — иначе будет вспышка не той темы.
(function () {{
  try {{
    var t = localStorage.getItem('zhpl:theme');
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
  }} catch (e) {{}}
}})();
</script>
</head>
<body>

<header class="masthead">
  <div class="wrap">
    <div class="masthead-top">
      <picture class="seal">
        <source srcset="../assets/logo-seal-dark.svg" media="(prefers-color-scheme: dark)" id="seal-dark-source">
        <img src="../assets/logo-seal.svg" alt="Печать журнала: Журнал Прикладной Лженауки, Институт Прикладной Метафизики" width="86" height="86">
      </picture>
      <div class="masthead-titles">
        <h1><a href="../index.html">Журнал Прикладной Лженауки</a></h1>
        <p class="affil">Институт Прикладной Метафизики · Кафедра тензорного анализа межличностных отношений</p>
      </div>
    </div>

    <nav class="top-nav">
      <a href="../index.html#issue">← Все статьи</a>
      <a href="../index.html#people">Авторы</a>
      <a href="../index.html#authors">Для авторов</a>
      <a href="https://github.com/DarthBeltazar/AbsoluteScience">Репозиторий</a>
      <button type="button" class="theme-toggle" id="theme-toggle-btn" aria-pressed="false" onclick="toggleTheme()">🌙 Тёмная тема</button>
    </nav>
  </div>
</header>

<main>
  <div class="wrap">
    <section id="article">
{body}
    </section>
  </div>
</main>

<footer>
  <div class="wrap">
    <p>Журнал Прикладной Лженауки · Институт Прикладной Метафизики</p>
    <p>ISSN 9999-9999 (online, вымышленный) · Рецензент 2 замечаний не имеет</p>
    <p><a href="https://github.com/DarthBeltazar/AbsoluteScience">github.com/DarthBeltazar/AbsoluteScience</a></p>
  </div>
</footer>

<script src="../assets/theme.js"></script>
<script src="../assets/reader.js"></script>
</body>
</html>
"""


def render_article_pages(manifest: dict) -> dict[str, str]:
    """{articles/<slug>.html: содержимое} для КАЖДОЙ статьи, включая скрытые."""
    return {
        f"articles/{art['id']}.html": render_article_page(art)
        for art in manifest["articles"]
    }


# ---------- Счётчики статей у авторов (карточки #people) ----------

def person_article_count(person_name: str, articles: list[dict]) -> int:
    return sum(1 for a in articles if person_name in a["authors"])


def render_people_stats(manifest: dict, text: str) -> str:
    """Подставить в карточки #people число статей на автора — считается из
    articles.json (совпадение полного имени в поле "authors"), а не хранится
    руками: раньше это число надо было чинить отдельным коммитом каждый раз,
    когда статью скрывали/публиковали."""
    articles = visible_articles(manifest)
    for person in manifest.get("people", []):
        count = person_article_count(person["name"], articles)
        word = ru_count(count, "статья", "статьи", "статей")
        inner = f"<strong>{count}</strong> {word}"
        text = replace_region(text, f"STAT:person:{person['id']}", inner, block=False)
    return text


# ---------- sitemap.xml ----------

def render_sitemap(manifest: dict) -> str:
    """sitemap.xml: главная страница + страница и PDF каждой видимой статьи
    (скрытые — не рекламируем поисковикам, хотя файлы и остаются доступны по
    прямой ссылке)."""
    urls = [BASE_URL]
    for art in visible_articles(manifest):
        urls.append(f"{BASE_URL}articles/{art['id']}.html")
        urls.append(f"{BASE_URL}articles/{art['id']}.pdf")
    entries = "\n".join(f"  <url>\n    <loc>{u}</loc>\n  </url>" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )


# ---------- index.html: замена именованных областей ----------

def replace_region(text: str, name: str, inner: str, *, block: bool) -> str:
    """Заменить содержимое между парными маркерами-комментариями.

    block=True   : <!-- name:START --> ... <!-- name:END -->  (многострочный блок)
    block=False  : <!-- name --> ... <!-- /name -->           (инлайновое значение)
    """
    if block:
        open_m, close_m = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
        # closing marker keeps the section's 6-space indent (see index.html)
        repl = f"{open_m}\n{inner}\n      {close_m}"
    else:
        open_m, close_m = f"<!-- {name} -->", f"<!-- /{name} -->"
        repl = f"{open_m}{inner}{close_m}"

    pattern = re.compile(
        re.escape(open_m) + r".*?" + re.escape(close_m), re.DOTALL
    )
    if not pattern.search(text):
        sys.exit(f"error: в index.html не найдены маркеры {open_m} … {close_m}")
    return pattern.sub(lambda _: repl, text, count=1)


def build(manifest: dict, current: str) -> str:
    out = replace_region(current, "ARTICLES", render_articles(manifest), block=True)
    out = replace_region(
        out, "STAT:articles", str(len(visible_articles(manifest))), block=False
    )
    journal = manifest.get("journal", {})
    if "volume" in journal:
        out = replace_region(out, "STAT:volume", str(journal["volume"]), block=False)
    if "volume" in journal and "year" in journal:
        heading = f'Том {journal["volume"]} · {journal["year"]}'
        out = replace_region(out, "ISSUE-HEADING", heading, block=False)
    out = render_people_stats(manifest, out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="не писать; выйти с кодом 1, если сгенерированные файлы не совпадают с манифестом",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    current_index = INDEX.read_text(encoding="utf-8")
    updated_index = build(manifest, current_index)

    current_sitemap = SITEMAP.read_text(encoding="utf-8") if SITEMAP.exists() else None
    updated_sitemap = render_sitemap(manifest)

    updated_pages = render_article_pages(manifest)
    stale_pages = []
    for rel_path, content in updated_pages.items():
        path = ROOT / rel_path
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            stale_pages.append((path, content))

    index_stale = updated_index != current_index
    sitemap_stale = updated_sitemap != current_sitemap

    if not index_stale and not sitemap_stale and not stale_pages:
        print("index.html, articles/*.html и sitemap.xml уже синхронны с articles/articles.json")
        return 0

    if args.check:
        if index_stale:
            print("index.html устарел: запустите `python scripts/gen_site.py`", file=sys.stderr)
        for path, _ in stale_pages:
            print(f"{path.relative_to(ROOT)} устарел: запустите `python scripts/gen_site.py`", file=sys.stderr)
        if sitemap_stale:
            print("sitemap.xml устарел: запустите `python scripts/gen_site.py`", file=sys.stderr)
        return 1

    if index_stale:
        INDEX.write_text(updated_index, encoding="utf-8")
    for path, content in stale_pages:
        path.write_text(content, encoding="utf-8")
    if sitemap_stale:
        SITEMAP.write_text(updated_sitemap, encoding="utf-8")

    shown = len(visible_articles(manifest))
    hidden = len(manifest["articles"]) - shown
    note = f", скрыто {hidden}" if hidden else ""
    print(f"index.html, {len(updated_pages)} страниц статей и sitemap.xml обновлены ({shown} статей{note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
