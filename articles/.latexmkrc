# Build every article in this directory with XeLaTeX (Cyrillic via fontspec +
# polyglossia — pdflatex will not work). latexmk decides how many passes are
# needed for cross-references, the theorem counters and the page ranges.
#
# Usage:  cd articles && latexmk          # build all *.tex
#         cd articles && latexmk -c       # remove build artifacts (keep PDFs)

$pdf_mode = 5;   # 5 = XeLaTeX
$xelatex  = 'xelatex -interaction=nonstopmode -halt-on-error -synctex=1 %O %S';

# Build the real articles (light + dark variant of each); template.tex is a
# scaffold, not a publication. The .dark.tex wrappers reuse the main source.
@default_files = (
  'tenzornaya_psikhometriya.tex', 'tenzornaya_psikhometriya.dark.tex',
  'termodinamika_burmaldy.tex',   'termodinamika_burmaldy.dark.tex',
);

# Keep .synctex.gz out of the way but next to the PDF is fine; the repo
# .gitignore already excludes all the intermediate files listed below.
$clean_ext = 'synctex.gz synctex.gz(busy) run.xml bcf xdv fls fdb_latexmk';
