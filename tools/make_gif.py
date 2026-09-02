"""Turn a folder of photos into a GIF.

Made for phone pictures: reads JPG/PNG/WEBP, and HEIC (iPhone) via pillow-heif.
Respects EXIF rotation, downscales frames so the GIF stays web-sized, and
letterboxes mixed portrait/landscape shots onto a common canvas.

Usage:
    python tools/make_gif.py <photo folder> [out.gif] [--width 640] [--ms 150]

Frames go in filename order (phone filenames sort chronologically).
--width  max frame width in px (default 640 — good for the site)
--ms     time each frame shows, in milliseconds (default 150)
"""
import argparse
from pathlib import Path

from PIL import Image, ImageOps

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_OK = True
except ImportError:
    HEIC_OK = False

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def main():
    ap = argparse.ArgumentParser(description="Make a GIF from a folder of photos.")
    ap.add_argument("folder", type=Path, help="folder containing the photos")
    ap.add_argument("out", type=Path, nargs="?", default=Path("out.gif"))
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--ms", type=int, default=150)
    args = ap.parse_args()

    files = sorted(p for p in args.folder.iterdir() if p.suffix.lower() in EXTS)
    if not HEIC_OK:
        heic = [p for p in files if p.suffix.lower() == ".heic"]
        if heic:
            print(f"note: skipping {len(heic)} .heic file(s) — run `pip install pillow-heif` to include them")
            files = [p for p in files if p.suffix.lower() != ".heic"]
    if not files:
        raise SystemExit(f"no images found in {args.folder}")

    frames = []
    for p in files:
        img = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        img.thumbnail((args.width, args.width * 4))
        frames.append(img)
        print(f"  {p.name}  ->  {img.size[0]}x{img.size[1]}")

    if len({f.size for f in frames}) > 1:
        w = max(f.size[0] for f in frames)
        h = max(f.size[1] for f in frames)
        print(f"mixed sizes — letterboxing all frames to {w}x{h}")
        frames = [ImageOps.pad(f, (w, h), color="black") for f in frames]

    frames[0].save(args.out, save_all=True, append_images=frames[1:],
                   duration=args.ms, loop=0, optimize=True)
    kb = args.out.stat().st_size / 1024
    print(f"wrote {args.out} — {len(frames)} frames, {kb:,.0f} KB")


if __name__ == "__main__":
    main()
