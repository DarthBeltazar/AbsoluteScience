# Журнал Прикладной Лженауки — сборка
#
#   make           собрать статьи и пересобрать сайт
#   make articles  только PDF (latexmk + XeLaTeX, см. articles/.latexmkrc)
#   make site      только index.html из articles/articles.json
#   make check     проверить, что сайт синхронен с манифестом (для CI)
#   make clean     удалить промежуточные файлы LaTeX (PDF остаются)

PYTHON ?= python

.PHONY: all articles site check clean

all: articles site

articles:
	cd articles && latexmk

site:
	$(PYTHON) scripts/gen_site.py

check:
	$(PYTHON) scripts/gen_site.py --check

clean:
	cd articles && latexmk -c
