<#
.SYNOPSIS
    Сборка «Журнала Прикладной Лженауки» на Windows (аналог Makefile для тех, у кого нет make).

.DESCRIPTION
    Без параметров: собирает статьи (latexmk + XeLaTeX) и пересобирает index.html из
    articles/articles.json.

.PARAMETER ArticlesOnly
    Только компиляция PDF.

.PARAMETER SiteOnly
    Только регенерация index.html.

.PARAMETER Check
    Не писать файлы, а проверить, что index.html синхронен с манифестом; ненулевой
    код возврата, если нет.

.EXAMPLE
    .\build.ps1
    .\build.ps1 -ArticlesOnly
    .\build.ps1 -SiteOnly
#>
[CmdletBinding()]
param(
    [switch]$ArticlesOnly,
    [switch]$SiteOnly,
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = if ($env:PYTHON) { $env:PYTHON } else { 'python' }

function Invoke-Articles {
    Write-Host '==> Компиляция статей (latexmk)' -ForegroundColor Cyan
    Push-Location (Join-Path $root 'articles')
    try { & latexmk; if ($LASTEXITCODE -ne 0) { throw "latexmk завершился с кодом $LASTEXITCODE" } }
    finally { Pop-Location }
}

function Invoke-Site {
    param([switch]$CheckOnly)
    $script = Join-Path $root 'scripts/gen_site.py'
    if ($CheckOnly) {
        Write-Host '==> Проверка синхронности index.html' -ForegroundColor Cyan
        & $python $script --check
    } else {
        Write-Host '==> Регенерация index.html из articles/articles.json' -ForegroundColor Cyan
        & $python $script
    }
    if ($LASTEXITCODE -ne 0) { throw "gen_site.py завершился с кодом $LASTEXITCODE" }
}

if ($Check)              { Invoke-Site -CheckOnly; return }
if (-not $SiteOnly)      { Invoke-Articles }
if (-not $ArticlesOnly)  { Invoke-Site }
Write-Host 'Готово.' -ForegroundColor Green
