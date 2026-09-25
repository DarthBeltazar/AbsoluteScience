#!/usr/bin/env python3
"""Отрисовать PNG-превью статей для соцсетей: assets/og/<slug>.png.

SVG-карточку каждой статьи строит gen_site.render_og_svg() из
articles/articles.json; этот скрипт растеризует её headless-браузером
(Chrome/Chromium/Edge) и записывает в PNG хэш исходного SVG (чанк tEXt
«zhpl-svg-sha256»). `gen_site.py --check` сверяет этот хэш с текущим SVG,
так что после правки заголовка, авторов или DOI CI укажет на устаревшее
превью. Перерисовываются только устаревшие карточки (или все с --force).

Растеризовать нужно локально, а не в CI: карточка набрана Georgia, а на
ubuntu-latest её нет (и кириллица ушла бы в запасной шрифт). Не sips —
см. CLAUDE.md про растеризацию SVG.

Браузер ищется в переменной окружения CHROME, затем в PATH, затем в
стандартных путях установки на Windows и macOS.

Использование:
    python scripts/render_og.py            # перерисовать отсутствующие/устаревшие
    python scripts/render_og.py --force    # перерисовать все
"""
from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_site  # noqa: E402

WIDTH, HEIGHT = 1200, 630

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]


def find_browser() -> str:
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    for path in BROWSER_CANDIDATES:
        if Path(path).exists():
            return path
    sys.exit("error: не найден Chrome/Chromium/Edge — укажите путь в переменной CHROME")


def png_size(data: bytes) -> tuple[int, int]:
    return struct.unpack(">II", data[16:24])  # IHDR сразу после сигнатуры


def with_text_chunk(data: bytes, key: bytes, value: str) -> bytes:
    """Вставить tEXt-чанк key=value перед IEND."""
    payload = key + b"\0" + value.encode("latin-1")
    chunk = (
        struct.pack(">I", len(payload))
        + b"tEXt"
        + payload
        + struct.pack(">I", zlib.crc32(b"tEXt" + payload) & 0xFFFFFFFF)
    )
    iend = data.rindex(b"IEND") - 4  # начало чанка IEND (с полем длины)
    return data[:iend] + chunk + data[iend:]


def rasterize(browser: str, svg: str, tmp: Path) -> bytes:
    src = tmp / "card.svg"
    out = tmp / "card.png"
    src.write_text(svg, encoding="utf-8")
    out.unlink(missing_ok=True)
    subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--window-size={WIDTH},{HEIGHT}",
            f"--user-data-dir={tmp / 'profile'}",
            f"--screenshot={out}",
            src.as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=120,
    )
    data = out.read_bytes()
    size = png_size(data)
    if size != (WIDTH, HEIGHT):
        sys.exit(f"error: браузер отдал {size[0]}×{size[1]} вместо {WIDTH}×{HEIGHT}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="перерисовать все превью")
    args = parser.parse_args()

    manifest = gen_site.json.loads(gen_site.MANIFEST.read_text(encoding="utf-8"))
    gen_site.OG_DIR.mkdir(parents=True, exist_ok=True)
    browser = None
    rendered = 0

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        for art in manifest["articles"]:
            svg = gen_site.render_og_svg(art, manifest)
            digest = gen_site.og_svg_hash(svg)
            path = gen_site.OG_DIR / f"{art['id']}.png"
            if not args.force and gen_site.png_text_chunk(path, gen_site.OG_HASH_KEY) == digest:
                continue
            browser = browser or find_browser()
            png = rasterize(browser, svg, tmp)
            path.write_bytes(with_text_chunk(png, gen_site.OG_HASH_KEY, digest))
            print(f"{path.relative_to(gen_site.ROOT).as_posix()} отрисован")
            rendered += 1

    if not rendered:
        print("все превью в assets/og/ актуальны")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
