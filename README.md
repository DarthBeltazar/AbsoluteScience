# Журнал Прикладной Лженауки

Репозиторий сатирического научного журнала: статьи переносят строгий аппарат точных наук
(тензорный анализ, термодинамика, теория игр…) на бытовые темы, сохраняя абсолютно серьёзный
академический тон. Всё содержимое вымышленное — это художественный проект, а не настоящие
исследования.

Сайт (GitHub Pages): <https://darthbeltazar.github.io/AbsoluteScience/>

## Структура

| Путь | Что это |
|---|---|
| `guide/zhurnal_prikladnoy_lzhenauki_guide.md` | Руководство для авторов — концепция, порядок разделов статьи, техтребования. Главный документ. |
| `articles/<slug>.tex` + `<slug>.pdf` | Исходник статьи и скомпилированный PDF (версионируется). |
| `articles/zhpl.sty` | Пакет журнала: преамбула, окружения теорем, макросы титульного блока. |
| `articles/template.tex` | Скелет новой статьи в порядке §2 руководства. |
| `articles/articles.json` | Единственный источник метаданных статей для сайта. |
| `index.html`, `assets/style.css` | Статический сайт журнала. Блок «Текущий номер» генерируется. |
| `scripts/gen_site.py` | Пересборка сайта из `articles.json`. |

## Сборка

Нужен **XeLaTeX** (кириллица через `fontspec` + `polyglossia`; pdfLaTeX не подходит) и Python 3.

```sh
make            # статьи + сайт
make articles   # только PDF  (cd articles && latexmk)
make site       # только index.html из articles/articles.json
make check      # проверить, что сайт синхронен с манифестом
```

Без `make` (Windows): `./build.ps1`, `./build.ps1 -ArticlesOnly`, `./build.ps1 -SiteOnly`.

## Как добавить статью

1. `cp articles/template.tex articles/<slug>.tex`, заполнить TODO по руководству §2.
2. `cd articles && latexmk` — собрать PDF. Закоммитить `.tex` и `.pdf`.
3. Дописать объект `<slug>` в `articles/articles.json`.
4. `python scripts/gen_site.py` — обновит карточки и счётчики в `index.html`.
   Размеченные `<!-- ARTICLES:START/END -->` и `<!-- STAT:… -->` области руками не трогать.

CI (`.github/workflows/build.yml`) собирает PDF на каждый push/PR, проверяет синхронность
сайта и публикует его на GitHub Pages из ветки `main`. Для Pages в настройках репозитория
должно быть выбрано **Settings → Pages → Source: GitHub Actions**.

Подробности по стилю и оформлению — в [руководстве для авторов](guide/zhurnal_prikladnoy_lzhenauki_guide.md);
заметки для Claude Code — в [`CLAUDE.md`](CLAUDE.md).
