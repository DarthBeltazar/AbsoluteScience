# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Content repository for **«Журнал Прикладной Лженауки»** (Journal of Applied Pseudoscience) — a
satirical academic journal that applies rigorous formal apparatus from the exact sciences (tensor
analysis, thermodynamics, GR, game theory…) to mundane everyday subjects, written in a completely
straight academic tone. It contains the published articles (LaTeX + compiled PDF) and a static
website. There is no application code, no package manager, no test suite.

Everything author-facing is in Russian. Keep that tone: articles never wink at the reader — the
humor comes from real, physically-meaningful math applied to a trivial subject.

## Layout

- `guide/zhurnal_prikladnoy_lzhenauki_guide.md` — **the authoritative spec.** Defines journal
  concept, the exact section order every article must follow, the LaTeX template, illustration
  precision rules, and the new-article checklist. Read this before writing or editing an article.
- `articles/<slug>.tex` + `articles/<slug>.pdf` — one article per slug; the `.pdf` is the
  compiled artifact and is committed alongside the source.
- `articles/zhpl.sty` — the journal's LaTeX package: fixed preamble, theorem environments, and
  macros for the title furniture (`\zhplsetup`, `\zhplauthors`, `\zhplbadges`, `\zhplciteas`,
  `\zhplgraphicabstract`, environments `zhplhighlights` / `zhplreviews` / `zhplsignificance`).
- `articles/template.tex` — compilable skeleton in guide §2 order; copy it to start a new article.
- `articles/articles.json` — **single source of truth** for article metadata shown on the site.
- `articles/.latexmkrc` — makes `latexmk` use XeLaTeX and build both articles.
- `scripts/gen_site.py` — regenerates the `#issue` cards and stat counters in `index.html` from
  `articles.json`; touches only the marked regions. `--check` fails if the file is out of date.
- `index.html` — static journal site (single page, no framework). Inline `<script>` handles the
  "Читать на сайте" PDF reader toggle; styling is in `assets/style.css`. The `#issue` cards and
  the `ОПУБЛИКОВАННЫЕ СТАТЬИ` / `ТОМ` counters live between `<!-- ARTICLES:START/END -->` and
  `<!-- STAT:… -->` markers and are generated — edit `articles.json`, not these regions.
- `assets/style.css` — hand-written CSS, design tokens in `:root`; dark theme via
  `prefers-color-scheme`, plus a `@media print` block.
- `Makefile` / `build.ps1` — `make` / `.\build.ps1` builds articles then the site.
- `.github/workflows/build.yml` — CI: compiles PDFs, runs `gen_site.py --check`, deploys the
  site to GitHub Pages on `main`.

## Building an article

Compile with **XeLaTeX** (Cyrillic via `fontspec` + `polyglossia` — pdflatex will fail):

```
cd articles && latexmk          # builds every *.tex; latexmk decides the pass count
```

Every `.tex` starts with `% !TeX program = xelatex` and does `\usepackage{zhpl}` — do not
re-copy the preamble or the colored boxes; use the `zhpl.sty` macros. Per guide §3, check the
log for `!` errors and large `Overfull \hbox`, and eyeball every page so formulas/figures/
captions don't collide. Commit the regenerated `.pdf` with the source.

## Adding a new article

1. `cp articles/template.tex articles/<slug>.tex`, fill in the TODOs (guide §2 order), then
   `cd articles && latexmk`. Commit `<slug>.tex` and `<slug>.pdf`.
2. Add a `<slug>` object to `articles/articles.json` (id, issue, kicker, titleHtml, authors,
   abstract, highlights, keywords, citeHtml, doi).
3. Run `python scripts/gen_site.py` (or `make site`) — it rebuilds the `#issue` cards, the
   `reader-N` ids, and the counters. Never hand-edit the generated regions of `index.html`.

## Cross-article conventions (must stay consistent)

Per guide §1, these recur verbatim across every article — match them exactly:

- Authors: **Роман Георгиевич Александров, Клод Соннет Антропикович**; affiliation Институт
  Прикладной Метафизики / Кафедра тензорного анализа межличностных отношений.
- Клод Соннет Антропикович's CRediT contribution is software / visualization / "техническая
  поддержка бесконечного терпения".
- Reviewer 2 always has no substantive comments; Impact Factor is `∞`.
- Fake DOI pattern: `10.9999/жпл.20XX.000N`.
- Bibliography is fictional; author surnames are derived from that article's own coined terms.
- Conflict-of-interest statement is "not declared" with a caveat citing one of the article's own
  (real, in-body) theorems.
- Each article ends its substantive part with a "Ограничения" section honestly admitting the
  result is useless, and the conclusion references "достаточное основание для дальнейшего финансирования".
