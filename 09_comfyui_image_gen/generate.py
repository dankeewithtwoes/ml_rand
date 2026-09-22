#!/usr/bin/env python3
"""Generate one image via ComfyUI API."""
import argparse, json, os, time, urllib.request
from pathlib import Path


PROMPT_TEMPLATE = {
    "3": {
        "inputs": {"seed": 0, "steps": 20, "cfg": 8.0, "sampler_name": "euler", "scheduler": "normal",
                   "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
                   "latent_image": ["5", 0]},
        "class_type": "KSampler",
    },
    "4": {"inputs": {"ckpt_name": "model.safetensors"}, "class_type": "CheckpointLoaderSimple"},
    "5": {"inputs": {"width": 512, "height": 512, "batch_size": 1}, "class_type": "EmptyLatentImage"},
    "6": {"inputs": {"text": "beautiful scenery", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
    "7": {"inputs": {"text": "text, watermark", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
    "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
    "9": {"inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]}, "class_type": "SaveImage"},
}


def queue_prompt(server: str, prompt: dict):
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(
        f"{server}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def get_history(server: str, prompt_id: str, timeout: int = 300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{server}/history/{prompt_id}", timeout=10) as resp:
                data = json.loads(resp.read())
            if prompt_id in data and data[prompt_id].get("outputs"):
                return data[prompt_id]
        except Exception:
            pass
        time.sleep(0.5)
    return None


def fetch_image(server: str, filename: str, subfolder: str, folder_type: str, output_dir: Path):
    params = f"filename={filename}&subfolder={subfolder}&type={folder_type}"
    url = f"{server}/view?{params}"
    data = urllib.request.urlopen(url, timeout=30).read()
    out = output_dir / filename
    out.write_bytes(data)
    return out


def build_prompt(positive: str, negative: str, seed: int, width: int, height: int, steps: int, cfg: float):
    p = json.loads(json.dumps(PROMPT_TEMPLATE))
    p["3"]["inputs"]["seed"] = seed
    p["3"]["inputs"]["steps"] = steps
    p["3"]["inputs"]["cfg"] = cfg
    p["5"]["inputs"]["width"] = width
    p["5"]["inputs"]["height"] = height
    p["6"]["inputs"]["text"] = positive
    p["7"]["inputs"]["text"] = negative
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default=os.getenv("COMFYUI_SERVER", "http://127.0.0.1:8188"))
    parser.add_argument("--prompt", default="a robot reading a book, digital art")
    parser.add_argument("--negative", default="blurry, low quality")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--cfg", type=float, default=8.0)
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_prompt(args.prompt, args.negative, args.seed, args.width, args.height, args.steps, args.cfg)
    try:
        res = queue_prompt(args.server, prompt)
    except Exception as exc:
        print(f"[skip] ComfyUI not reachable: {exc}")
        return

    prompt_id = res["prompt_id"]
    history = get_history(args.server, prompt_id)
    if not history:
        print("Timeout waiting for ComfyUI")
        return

    for node_id, node_output in history["outputs"].items():
        for img in node_output.get("images", []):
            path = fetch_image(args.server, img["filename"], img.get("subfolder", ""), img["type"], output_dir)
            print(f"Saved {path}")


if __name__ == "__main__":
    main()
