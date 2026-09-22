#!/usr/bin/env python3
"""Export the trained PyTorch model to ONNX."""

import argparse

import torch
import yaml

from src.model import TwoLayerNet


def main(config_path: str, model_path: str, output_path: str):
    cfg = yaml.safe_load(open(config_path))
    model = TwoLayerNet(**cfg["model"])
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model.eval()

    dummy_input = torch.randn(1, cfg["model"]["input_dim"])
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        input_names=["features"],
        output_names=["logits"],
        dynamic_axes={"features": {0: "batch_size"}, "logits": {0: "batch_size"}},
        opset_version=11,
    )
    print(f"ONNX model saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--model", default="demo/model.pt")
    parser.add_argument("--output", default="demo/model.onnx")
    args = parser.parse_args()
    main(args.config, args.model, args.output)
