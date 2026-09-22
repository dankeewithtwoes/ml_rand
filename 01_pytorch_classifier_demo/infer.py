#!/usr/bin/env python3
"""Run inference with a trained PyTorch model."""

import argparse

import torch
import yaml

from src.model import TwoLayerNet


CLASSES = {0: "class_a", 1: "class_b"}


def main(config_path: str, model_path: str, input_str: str):
    cfg = yaml.safe_load(open(config_path))
    model = TwoLayerNet(**cfg["model"])
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model.eval()

    x = torch.tensor([float(v) for v in input_str.split(",")], dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        logits = model(x)
        prob = torch.softmax(logits, dim=1)
        pred = logits.argmax(dim=1).item()

    print(f"Input: {x.squeeze(0).tolist()}")
    print(f"Prediction: {CLASSES[pred]} (class {pred})")
    print(f"Probabilities: {prob.squeeze(0).tolist()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--model", default="demo/model.pt")
    parser.add_argument("--input", default="0.5,-0.3", help='Comma-separated features, e.g. "0.5,-0.3"')
    args = parser.parse_args()
    main(args.config, args.model, args.input)
