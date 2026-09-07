# Build every article in this directory with XeLaTeX (Cyrillic via fontspec +
# polyglossia — pdflatex will not work). latexmk decides how many passes are
# needed for cross-references, the theorem counters and the page ranges.
#
# Usage:  cd articles && latexmk          # build all *.tex
#         cd articles && latexmk -c       # remove build artifacts (keep PDFs)

$pdf_mode = 5;   # 5 = XeLaTeX
$xelatex  = 'xelatex -interaction=nonstopmode -halt-on-error -synctex=1 %O %S';

# Build every real article (light + its .dark wrapper) found in this directory,
# so a newly added <slug>.tex/<slug>.dark.tex pair is picked up automatically —
# nothing to add here. template.tex is a scaffold, not a publication, so it's
# the one name excluded.
opendir(my $dh, '.') or die "articles/.latexmkrc: can't read articles/: $!";
@default_files = sort grep { /\.tex$/ && $_ ne 'template.tex' } readdir($dh);
closedir($dh);

# Keep .synctex.gz out of the way but next to the PDF is fine; the repo
# .gitignore already excludes all the intermediate files listed below.
$clean_ext = 'synctex.gz synctex.gz(busy) run.xml bcf xdv fls fdb_latexmk';
