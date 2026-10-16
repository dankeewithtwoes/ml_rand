#!/usr/bin/env python3
"""Generate one image via ComfyUI API."""
import argparse, json, os, time, urllib.request
from pathlib import Path
from urllib.parse import urlencode


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
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with urllib.request.urlopen(f"{server.rstrip('/')}/history/{prompt_id}", timeout=min(10, timeout)) as resp:
            data = json.loads(resp.read())
        history = data.get(prompt_id, {})
        if history.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"ComfyUI execution failed: {history['status'].get('messages', [])}")
        if history.get("outputs"):
            return history
        time.sleep(0.5)
    raise TimeoutError("Timed out waiting for ComfyUI")


def fetch_image(server: str, filename: str, subfolder: str, folder_type: str, output_dir: Path):
    if not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
        raise ValueError("ComfyUI image filename must not contain a path")
    params = urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
    url = f"{server}/view?{params}"
    data = urllib.request.urlopen(url, timeout=30).read()
    out = output_dir / filename
    output_dir.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return out


def build_prompt(positive: str, negative: str, seed: int, width: int, height: int, steps: int, cfg: float, checkpoint: str | None = None):
    p = json.loads(json.dumps(PROMPT_TEMPLATE))
    p["3"]["inputs"]["seed"] = seed
    p["3"]["inputs"]["steps"] = steps
    p["3"]["inputs"]["cfg"] = cfg
    p["5"]["inputs"]["width"] = width
    p["5"]["inputs"]["height"] = height
    p["6"]["inputs"]["text"] = positive
    p["7"]["inputs"]["text"] = negative
    if checkpoint:
        p["4"]["inputs"]["ckpt_name"] = checkpoint
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
    parser.add_argument("--checkpoint", help="checkpoint filename installed in ComfyUI")
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_prompt(args.prompt, args.negative, args.seed, args.width, args.height, args.steps, args.cfg, args.checkpoint)
    try:
        res = queue_prompt(args.server, prompt)
    except Exception as exc:
        parser.exit(2, f"ComfyUI request failed: {exc}\n")

    prompt_id = res["prompt_id"]
    history = get_history(args.server, prompt_id, args.timeout)

    saved = 0
    for node_id, node_output in history["outputs"].items():
        for img in node_output.get("images", []):
            path = fetch_image(args.server, img["filename"], img.get("subfolder", ""), img["type"], output_dir)
            print(f"Saved {path}")
            saved += 1
    if not saved:
        parser.exit(2, "ComfyUI returned no images\n")


if __name__ == "__main__":
    main()
