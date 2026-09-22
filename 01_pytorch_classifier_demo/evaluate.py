#!/usr/bin/env python3
"""Evaluate a trained model and print a classification report."""

import argparse

import torch
import yaml
from omegaconf import OmegaConf
from sklearn.metrics import classification_report

from src.data import get_datasets
from src.model import TwoLayerNet
from src.utils import set_seed


def main(config_path: str, model_path: str):
    # OmegaConf: get_datasets expects attribute access (cfg.data.n_samples),
    # matching the DictConfig that train.py passes under Hydra.
    cfg = OmegaConf.create(yaml.safe_load(open(config_path)))
    set_seed(cfg.seed)

    _, val_ds = get_datasets(cfg)
    X_val, y_val = val_ds.tensors

    model = TwoLayerNet(**cfg.model)
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model.eval()

    with torch.no_grad():
        preds = model(X_val).argmax(dim=1).numpy()

    print(classification_report(y_val.numpy(), preds, target_names=["class_a", "class_b"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--model", default="demo/model.pt")
    args = parser.parse_args()
    main(args.config, args.model)
