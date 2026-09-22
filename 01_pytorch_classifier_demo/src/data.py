import numpy as np
import torch
from torch.utils.data import TensorDataset


def make_moons(n_samples: int = 1000, noise: float = 0.1):
    """Generate a synthetic two-moons dataset."""
    n = n_samples // 2
    t = np.linspace(0, np.pi, n)
    x1 = np.column_stack((np.cos(t), np.sin(t))) + np.random.randn(n, 2) * noise
    x2 = np.column_stack((1 - np.cos(t), 0.5 - np.sin(t))) + np.random.randn(n, 2) * noise
    X = np.vstack((x1, x2)).astype(np.float32)
    y = np.hstack((np.zeros(n), np.ones(n))).astype(np.int64)
    # Shuffle before splitting: raw moons are ordered class-0 then class-1,
    # so a naive tail split would put a single class in validation.
    # np.random is seeded by src.utils.set_seed, so the permutation is reproducible.
    order = np.random.permutation(len(X))
    return X[order], y[order]


def get_datasets(cfg):
    X, y = make_moons(n_samples=cfg.data.n_samples, noise=cfg.data.noise)
    split = int((1 - cfg.data.test_ratio) * len(X))
    X_train, y_train = torch.tensor(X[:split]), torch.tensor(y[:split])
    X_val, y_val = torch.tensor(X[split:]), torch.tensor(y[split:])
    return TensorDataset(X_train, y_train), TensorDataset(X_val, y_val)
