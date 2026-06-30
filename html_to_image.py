"""
html_to_image.py

Renders an HTML file to a full-page PNG and/or JPEG screenshot using a real
headless browser (Playwright + Chromium). This handles modern CSS properly:
grid/flexbox layouts, @font-face / Google Fonts, emoji, gradients, shadows, etc.

ONE-TIME SETUP
    pip install playwright pillow
    playwright install chromium      # downloads the browser binary (~150MB)

USAGE
    python html_to_image.py path/to/file.html
    python html_to_image.py path/to/file.html --out calendar --width 1200
    python html_to_image.py path/to/file.html --formats png jpg --scale 2

ARGUMENTS
    html_path        Path to the local HTML file to render
    --out            Output filename without extension (default: same as input)
    --width           Browser viewport width in px (default: 1200)
    --scale          Device scale factor, e.g. 2 = retina-quality (default: 2)
    --formats        One or more of: png jpg  (default: png jpg)
    --jpeg-quality   JPEG quality 1-100 (default: 92)
    --wait           Extra milliseconds to wait before screenshotting,
                      useful if the page has fonts/images that load async
                      (default: 300)
"""

import argparse
import sys
from pathlib import Path


def html_to_image(
    html_path: str,
    out_base: str | None = None,
    width: int = 1200,
    scale: float = 2,
    formats=("png", "jpg"),
    jpeg_quality: int = 92,
    wait_ms: int = 300,
):
    from playwright.sync_api import sync_playwright

    html_path = Path(html_path).resolve()
    if not html_path.exists():
        raise FileNotFoundError(f"Could not find HTML file: {html_path}")

    out_base = Path(out_base) if out_base else html_path.with_suffix("")
    png_path = out_base.with_suffix(".png")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": 800},  # height auto-grows below
            device_scale_factor=scale,
        )
        page.goto(html_path.as_uri())
        page.wait_for_timeout(wait_ms)  # let web fonts / images settle

        # Always take a full-page PNG first; it's lossless and becomes the
        # source for any JPEG conversion below.
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()

    print(f"Saved {png_path}")

    if "jpg" in formats or "jpeg" in formats:
        from PIL import Image

        jpg_path = out_base.with_suffix(".jpg")
        img = Image.open(png_path).convert("RGB")  # drop alpha for JPEG
        img.save(jpg_path, "JPEG", quality=jpeg_quality)
        print(f"Saved {jpg_path}")

    if "png" not in formats:
        png_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Convert an HTML file to PNG/JPEG.")
    parser.add_argument("html_path", help="Path to the HTML file to render")
    parser.add_argument("--out", default=None, help="Output filename without extension")
    parser.add_argument("--width", type=int, default=1200, help="Viewport width in px")
    parser.add_argument("--scale", type=float, default=2, help="Device scale factor (2 = retina)")
    parser.add_argument(
        "--formats", nargs="+", default=["png", "jpg"], choices=["png", "jpg", "jpeg"],
        help="Which output formats to save",
    )
    parser.add_argument("--jpeg-quality", type=int, default=92, help="JPEG quality 1-100")
    parser.add_argument("--wait", type=int, default=300, help="Extra ms to wait before capture")
    args = parser.parse_args()

    html_to_image(
        html_path=args.html_path,
        out_base=args.out,
        width=args.width,
        scale=args.scale,
        formats=args.formats,
        jpeg_quality=args.jpeg_quality,
        wait_ms=args.wait,
    )


if __name__ == "__main__":
    sys.exit(main())
