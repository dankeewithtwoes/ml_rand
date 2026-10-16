#!/usr/bin/env python3
"""Generate a grid of images with prompt variations via ComfyUI."""
import argparse, json, os, time
from pathlib import Path
from PIL import Image
import generate


PROMPT_VARIATIONS = [
    "a robot reading a book, digital art",
    "a robot reading a book, watercolor painting",
    "a robot reading a book, cyberpunk neon",
    "a robot reading a book, oil on canvas",
]


def create_grid(image_paths, output: Path, cols: int = 2):
    if not image_paths or cols <= 0:
        raise ValueError("a grid needs images and a positive column count")
    imgs = []
    for path in image_paths:
        with Image.open(path) as source:
            imgs.append(source.convert("RGB"))
    w = max(im.width for im in imgs)
    h = max(im.height for im in imgs)
    rows = (len(imgs) + cols - 1) // cols
    grid = Image.new("RGB", (w * cols, h * rows))
    for i, im in enumerate(imgs):
        x = (i % cols) * w
        y = (i // cols) * h
        grid.paste(im, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    grid.save(output)
    for image in imgs:
        image.close()
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default=os.getenv("COMFYUI_SERVER", "http://127.0.0.1:8188"))
    parser.add_argument("--prompts", default=",".join(PROMPT_VARIATIONS), help="comma-separated prompts")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--grid", default="outputs/grid.jpg")
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--checkpoint")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prompts = [p.strip() for p in args.prompts.split(",")]
    image_paths = []
    failures = []
    for idx, prompt in enumerate(prompts):
        try:
            p = generate.build_prompt(prompt, "blurry", seed=42 + idx, width=512, height=512, steps=20, cfg=8.0, checkpoint=args.checkpoint)
            res = generate.queue_prompt(args.server, p)
            history = generate.get_history(args.server, res["prompt_id"])
            if not history:
                continue
            for node_id, node_output in history["outputs"].items():
                for img in node_output.get("images", []):
                    path = generate.fetch_image(args.server, img["filename"], img.get("subfolder", ""), img["type"], output_dir)
                    image_paths.append(path)
                    print(f"Saved {path}")
        except Exception as exc:
            failures.append({"prompt": idx, "error": str(exc)})

    if image_paths:
        grid_path = create_grid(image_paths, Path(args.grid), args.cols)
        print(f"Grid saved {grid_path}")
        # Save metadata
        meta = {"prompts": prompts, "images": [str(p) for p in image_paths], "grid": str(grid_path)}
        Path(args.grid).with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    if failures or not image_paths:
        parser.exit(2, f"Batch generation incomplete: {failures or 'no images'}\n")


if __name__ == "__main__":
    main()
