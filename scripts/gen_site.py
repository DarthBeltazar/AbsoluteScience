#!/usr/bin/env python3
"""Пересобрать блок «Текущий номер» и счётчики в index.html из articles/articles.json.

articles.json — единственный источник правды по метаданным статей. Сайт их больше
не хранит вручную. Скрипт трогает только области между маркерами:

    <!-- ARTICLES:START --> ... <!-- ARTICLES:END -->   — карточки статей
    <!-- STAT:articles --> ... <!-- /STAT:articles -->   — число опубликованных статей
    <!-- STAT:volume --> ... <!-- /STAT:volume -->       — номер тома
    <!-- ISSUE-HEADING --> ... <!-- /ISSUE-HEADING -->   — «Том N · YYYY»

Остальная разметка не изменяется.

Использование:
    python scripts/gen_site.py            # переписать index.html
    python scripts/gen_site.py --check    # не писать; код возврата 1, если файл устарел
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


def short_title(title_html: str) -> str:
    """Часть заголовка до двоеточия, без тегов — для атрибута title у <iframe>."""
    text = re.sub(r"<[^>]+>", " ", title_html)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.split(":", 1)[0].strip()


def render_article(art: dict, n: int) -> str:
    """Одна карточка <article>. n — порядковый номер (для id reader-N)."""
    kicker = html.escape(art["kicker"])
    title_html = art["titleHtml"]  # намеренно содержит <br>, вставляется как есть
    authors = html.escape(art["authors"])
    abstract = html.escape(art["abstract"])
    cite_html = art["citeHtml"]    # содержит <em>, как есть
    doi = html.escape(art["doi"])
    art_id = art["id"]
    pdf = f"articles/{art_id}.pdf"
    tex = f"articles/{art_id}.tex"
    reader = f"reader-{n}"
    short = short_title(title_html)
    reader_name = html.escape(short)
    iframe_title = html.escape(f"{short} — полный текст")
    pdf_view = f"{pdf}#view=FitH"  # открывать по ширине страницы

    highlights = "\n".join(
        f"          <li>{h}</li>" for h in art["highlights"]  # <em>/<sub> допускаются
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
          <button type="button" class="btn read-btn" aria-expanded="false" onclick="toggleReader(this, '{reader}')">Читать на сайте</button>
          <a class="btn secondary" href="{pdf}">Скачать PDF</a>
          <a class="btn secondary" href="{tex}">Исходник (.tex)</a>
        </div>

        <div class="pdf-reader-wrap" id="{reader}-wrap" hidden>
          <div class="pdf-reader-bar">
            <span class="pdf-reader-name">{reader_name}</span>
            <button type="button" class="pdf-dark-btn" aria-pressed="false" onclick="togglePdfDark()">Тёмный PDF</button>
            <a class="pdf-reader-link" href="{pdf_view}" target="_blank" rel="noopener">Открыть отдельно ↗</a>
          </div>
          <iframe id="{reader}" class="pdf-reader" data-src="{pdf_view}"
                  title="{iframe_title}"></iframe>
        </div>
      </article>"""


def render_articles(manifest: dict) -> str:
    blocks = [
        render_article(art, i)
        for i, art in enumerate(manifest["articles"], start=1)
    ]
    return "\n\n".join(blocks)


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
        out, "STAT:articles", str(len(manifest["articles"])), block=False
    )
    journal = manifest.get("journal", {})
    if "volume" in journal:
        out = replace_region(out, "STAT:volume", str(journal["volume"]), block=False)
    if "volume" in journal and "year" in journal:
        heading = f'Том {journal["volume"]} · {journal["year"]}'
        out = replace_region(out, "ISSUE-HEADING", heading, block=False)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="не писать; выйти с кодом 1, если index.html не совпадает с манифестом",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    current = INDEX.read_text(encoding="utf-8")
    updated = build(manifest, current)

    if updated == current:
        print("index.html уже синхронен с articles/articles.json")
        return 0

    if args.check:
        print("index.html устарел: запустите `python scripts/gen_site.py`", file=sys.stderr)
        return 1

    INDEX.write_text(updated, encoding="utf-8")
    print(f"index.html обновлён ({len(manifest['articles'])} статей)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
