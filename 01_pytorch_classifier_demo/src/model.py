import torch
import torch.nn as nn


class TwoLayerNet(nn.Module):
    def __init__(self, input_dim: int = 2, hidden_dim: int = 16, num_classes: int = 2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
