#!/usr/bin/env python3
"""
color_at_luminance_backgrounds.py

Takes a folder of images and, for each one, builds a 1920x1080 canvas whose
background is the image's MEAN COLOR, rescaled so that the background's
luminance exactly equals the image's MEAN LUMINANCE. The original image is
then pasted centered at its native resolution.

In other words: the background carries the image's average hue, but sits at
the same brightness the neutral-gray (mean-luminance) background would have.
This keeps the light/luminance identical to the gray version while adding the
image's color.

Images larger than 1920x1080 are scaled down to fit (aspect ratio preserved).
Smaller images are scaled UP to fill a target fraction of the canvas (default
60%); images already at/above that size are left native. Nothing exceeds the
canvas.

Resizing never changes the background luminance: the background is always
computed from the original image's pixels, so the luminance match holds no
matter how the displayed image is scaled.

Outputs go to a "processed_color/" subfolder inside the input folder, each
file keeping its original name.

Usage:
    python color_at_luminance_backgrounds.py /path/to/img_folder
    python color_at_luminance_backgrounds.py /path/to/img_folder --fill 0.60
    python color_at_luminance_backgrounds.py /path/to/img_folder --fill 0   # no upscaling

    --fill F : scale images up to fill fraction F of the canvas (default 0.60).
               Already-larger images stay native. 0 disables upscaling.

Setup (one time, in Terminal):
    mamba create -n imgbg python=3.12 pillow numpy
    mamba activate imgbg
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

# Rec. 709 luma weights
WR, WG, WB = 0.2126, 0.7152, 0.0722


def luminance_of(rgb) -> float:
    r, g, b = rgb
    return WR * r + WG * g + WB * b


def color_at_luminance(img_rgb: Image.Image) -> tuple[int, int, int]:
    """Mean color of the image, rescaled to sit at the image's mean luminance.

    Returns an (R, G, B) whose own luminance == the image's mean luminance,
    while preserving the average hue (the R:G:B proportions). If scaling would
    clip a channel past 255, the color is clipped and the luminance is then
    nudged back onto target by blending toward gray as needed.
    """
    arr = np.asarray(img_rgb, dtype=np.float64)  # (H, W, 3)

    # Image's mean luminance (per-pixel luminance, then averaged) -- this is
    # the target, identical to what the gray-background script uses.
    lum_map = WR * arr[..., 0] + WG * arr[..., 1] + WB * arr[..., 2]
    L_target = float(lum_map.mean())

    # Mean color (average each channel).
    mean_rgb = arr.reshape(-1, 3).mean(axis=0)  # [R, G, B]
    L_color = luminance_of(mean_rgb)

    if L_color < 1e-6:
        # Degenerate (essentially black); just return gray at target.
        v = int(round(L_target))
        return (v, v, v)

    # Scale the mean color so its luminance matches L_target, keeping hue.
    scaled = mean_rgb * (L_target / L_color)

    # If any channel exceeds 255, we must clip -- but clipping changes the
    # luminance. To stay on target, blend the clipped color toward a gray of
    # luminance L_target by the minimum amount that brings all channels <= 255.
    if scaled.max() > 255.0:
        gray = np.array([L_target, L_target, L_target], dtype=np.float64)
        # Find smallest blend t in [0,1] toward gray s.t. all channels <= 255.
        # channel(t) = (1-t)*scaled + t*gray ; both scaled and gray have
        # luminance L_target, so the blend preserves luminance exactly.
        over = scaled > 255.0
        if over.any():
            # For each over-limit channel solve (1-t)*s + t*g = 255 for t.
            t_needed = (scaled[over] - 255.0) / (scaled[over] - gray[over])
            t = float(np.clip(t_needed.max(), 0.0, 1.0))
            scaled = (1 - t) * scaled + t * gray

    rgb = np.clip(np.round(scaled), 0, 255).astype(int)
    return (int(rgb[0]), int(rgb[1]), int(rgb[2]))


def fit_size(w: int, h: int, canvas_w: int, canvas_h: int,
             target_frac: float) -> tuple[int, int, str]:
    """Decide the placed size for an image, preserving aspect ratio.

    Rules, in order:
      1. If the image is larger than the canvas -> shrink to fit.
      2. Else scale the image UP until it fills `target_frac` of the canvas
         (measured on whichever dimension hits the fraction first), but never
         past the canvas and never shrinking an image that's already at/above
         the target.
      3. Images already at or above the target are left at native size.

    `target_frac` is a fraction of the canvas, e.g. 0.60 = fill 60%.
    Set target_frac <= 0 to disable upscaling entirely.

    Returns (new_w, new_h, action) for logging.
    """
    # 1. Too big -> shrink to fit.
    if w > canvas_w or h > canvas_h:
        scale = min(canvas_w / w, canvas_h / h)
        return max(1, round(w * scale)), max(1, round(h * scale)), "shrunk"

    if target_frac <= 0:
        return w, h, "native"

    # 2. How much would we need to scale so the image reaches target_frac of
    # the canvas on the dimension that limits it? Use the larger relative side
    # so the image grows until *one* side hits the target fraction.
    target_w = canvas_w * target_frac
    target_h = canvas_h * target_frac
    scale = max(target_w / w, target_h / h)

    # Only ever scale UP here; never shrink an already-large-enough image.
    if scale <= 1.0:
        return w, h, "native"

    # Cap so the upscaled image never exceeds the canvas.
    scale = min(scale, canvas_w / w, canvas_h / h)
    if scale <= 1.0:
        return w, h, "native"

    return round(w * scale), round(h * scale), f"upscaled x{scale:.2f}"


def process_image(src_path: Path, out_path: Path, canvas_w: int, canvas_h: int,
                  target_frac: float):
    with Image.open(src_path) as im:
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            white = Image.new("RGBA", im.size, (255, 255, 255, 255))
            im = Image.alpha_composite(white, im).convert("RGB")
        else:
            im = im.convert("RGB")

        # Background luminance is computed from the ORIGINAL image, so resizing
        # the displayed image never changes the luminance match.
        bg = color_at_luminance(im)
        canvas = Image.new("RGB", (canvas_w, canvas_h), bg)

        new_w, new_h, action = fit_size(
            im.width, im.height, canvas_w, canvas_h, target_frac
        )
        placed = im.copy()
        if (new_w, new_h) != (im.width, im.height):
            placed = placed.resize((new_w, new_h), Image.LANCZOS)

        x = (canvas_w - placed.width) // 2
        y = (canvas_h - placed.height) // 2
        canvas.paste(placed, (x, y))
        canvas.save(out_path)

        bg_lum = luminance_of(bg)
        return bg, bg_lum, placed.size, action


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("folder", type=Path, help="Folder containing images to process")
    p.add_argument("--width", type=int, default=1920, help="Canvas width in px (default: 1920)")
    p.add_argument("--height", type=int, default=1080, help="Canvas height in px (default: 1080)")
    p.add_argument("--out", default="processed_color",
                   help="Output subfolder name when nesting inside the input "
                        "folder (default: processed_color). Ignored if --outdir is set.")
    p.add_argument("--outdir", default=None,
                   help="Write outputs to THIS folder instead of inside the "
                        "input folder. A subfolder named after the input folder "
                        "is created inside it, so multiple input folders don't collide.")
    p.add_argument("--fill", type=float, default=0.60,
                   help="Scale images UP until they fill this fraction of the "
                        "canvas (default: 0.60 = 60%%). Images already at/above "
                        "this size stay native. Use 0 to disable upscaling.")
    args = p.parse_args()

    folder: Path = args.folder
    if not folder.is_dir():
        print(f"Error: {folder} is not a directory.", file=sys.stderr)
        return 1

    canvas_w, canvas_h = args.width, args.height
    if args.outdir:
        # Write into a brand-new destination folder, under a subfolder named
        # after the input folder so multiple runs stay separated.
        out_dir = Path(args.outdir) / folder.name
    else:
        out_dir = folder / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMG_EXTS
    )
    if not images:
        print(f"No images found in {folder}", file=sys.stderr)
        return 1

    print(f"Canvas: {canvas_w} x {canvas_h} px | background: mean color @ matched luminance")
    if args.fill > 0:
        print(f"Upscaling: images scaled up to fill {args.fill*100:.0f}% of canvas "
              f"(already-larger images kept native; capped to canvas)")
    print(f"Output folder: {out_dir}")
    print(f"Found {len(images)} image(s).\n")

    ok, failed = 0, 0
    for src in images:
        out_path = out_dir / src.name
        try:
            bg, bg_lum, size, action = process_image(
                src, out_path, canvas_w, canvas_h, args.fill
            )
            print(f"  \u2713 {src.name}: bg RGB={bg}, lum={bg_lum:6.2f}, "
                  f"placed {size[0]}x{size[1]} ({action})")
            ok += 1
        except Exception as e:
            print(f"  \u2717 {src.name}  ({e})", file=sys.stderr)
            failed += 1

    print(f"\nDone. {ok} processed, {failed} failed -> {out_dir}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
