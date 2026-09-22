#!/usr/bin/env python3
"""Config-driven PyTorch training harness with MLflow tracking."""

import csv
from pathlib import Path

import hydra
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from omegaconf import DictConfig
from torch.utils.data import DataLoader

from src.data import get_datasets
from src.model import TwoLayerNet
from src.utils import set_seed


try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


@hydra.main(version_base=None, config_path="configs", config_name="config")
def train(cfg: DictConfig):
    set_seed(cfg.seed)

    out_dir = Path(hydra.core.hydra_config.HydraConfig.get().runtime.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_ds, val_ds = get_datasets(cfg)
    train_loader = DataLoader(train_ds, batch_size=cfg.training.batch_size, shuffle=True)

    model = TwoLayerNet(**cfg.model)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.training.lr)

    if MLFLOW_AVAILABLE:
        mlflow.set_tracking_uri(f"file://{Path(cfg.logging.log_dir).resolve()}")
        mlflow.set_experiment(cfg.logging.experiment_name)
        mlflow.start_run()
        mlflow.log_params({"seed": cfg.seed, **cfg.training, **cfg.model, **cfg.data})

    X_val, y_val = val_ds.tensors
    history = []
    best_acc = 0.0

    for epoch in range(1, cfg.training.epochs + 1):
        model.train()
        for xb, yb in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_logits = model(X_val)
            val_loss = criterion(val_logits, y_val).item()
            preds = val_logits.argmax(dim=1)
            acc = (preds == y_val).float().mean().item()

        history.append({"epoch": epoch, "val_loss": val_loss, "val_acc": acc})
        if MLFLOW_AVAILABLE:
            mlflow.log_metrics({"val_loss": val_loss, "val_acc": acc}, step=epoch)

        if acc > best_acc:
            best_acc = acc
            torch.save(model.state_dict(), out_dir / "best_model.pt")

        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch {epoch:03d} | val_loss={val_loss:.4f} | val_acc={acc:.4f}")

    # Save final artifacts
    model_path = Path(cfg.output.model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), model_path)

    csv_path = out_dir / "history.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "val_loss", "val_acc"])
        writer.writeheader()
        writer.writerows(history)

    plot_path = Path(cfg.output.plot_path)
    plot_decision_boundary(model, val_ds.tensors[0].numpy(), val_ds.tensors[1].numpy(), plot_path)

    if MLFLOW_AVAILABLE:
        mlflow.log_artifact(str(csv_path))
        mlflow.log_artifact(str(plot_path))
        mlflow.log_artifact(str(model_path))
        mlflow.end_run()

    print(f"Best val_acc={best_acc:.4f}")
    print(f"Artifacts saved: {model_path}, {plot_path}, {csv_path}")


def plot_decision_boundary(model: nn.Module, X: np.ndarray, y: np.ndarray, path: Path):
    model.eval()
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02), np.arange(y_min, y_max, 0.02))
    grid = torch.tensor(np.c_[xx.ravel(), yy.ravel()], dtype=torch.float32)
    with torch.no_grad():
        Z = model(grid).argmax(dim=1).numpy()
    Z = Z.reshape(xx.shape)

    plt.figure(figsize=(6, 5))
    plt.contourf(xx, yy, Z, alpha=0.4, cmap="RdYlBu")
    plt.scatter(X[:, 0], X[:, 1], c=y, cmap="RdYlBu", edgecolors="k", s=20)
    plt.title("PyTorch classifier decision boundary")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


if __name__ == "__main__":
    train()
