#!/usr/bin/env python3
"""Launch a vLLM OpenAI-compatible server for throughput benchmarking."""
import argparse, subprocess, sys, time, urllib.request


def wait_for_server(base_url: str, timeout: int = 120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(base_url + "/health", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--dtype", default="auto")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--wait", action="store_true", help="Block until server healthy")
    args = parser.parse_args()

    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", args.model,
        "--port", str(args.port),
        "--max-model-len", str(args.max_model_len),
        "--dtype", args.dtype,
        "--gpu-memory-utilization", str(args.gpu_memory_utilization),
    ]
    print("[serve]", " ".join(cmd))
    proc = subprocess.Popen(cmd)
    if args.wait:
        base = f"http://localhost:{args.port}"
        if not wait_for_server(base):
            proc.terminate()
            raise RuntimeError("Server failed to start")
        print(f"[serve] healthy at {base}")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()
