from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def project_simplex(v: np.ndarray) -> np.ndarray:
    if len(v) == 1:
        return np.ones(1)
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u) - 1.0
    ind = np.arange(1, len(v) + 1)
    cond = u - cssv / ind > 0
    rho = ind[cond][-1]
    theta = cssv[cond][-1] / rho
    return np.maximum(v - theta, 0.0)


@dataclass
class LocalOptimizer:
    kind: str
    x: np.ndarray
    eta: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.999
    eps: float = 1e-8

    def __post_init__(self) -> None:
        self.anchor = self.x.copy()
        self.regret = np.zeros_like(self.x)
        self.m = np.zeros_like(self.x)
        self.v = np.zeros_like(self.x)
        self.vhat = np.zeros_like(self.x)
        self.t = 0

    @property
    def predictive(self) -> bool:
        return self.kind in {"ogd", "prm", "prm_plus"}

    def getx(self, predicted_grad: np.ndarray) -> np.ndarray:
        if self.kind in {"gd", "ogd"}:
            self.x = project_simplex(self.anchor + self.eta * predicted_grad)
        elif self.kind in {"rm", "rm_plus", "prm", "prm_plus"}:
            centered = predicted_grad - float(np.dot(predicted_grad, self.x))
            theta = np.maximum(self.regret + centered, 0.0)
            if theta.sum() > 0:
                self.x = theta / theta.sum()
        elif self.kind == "ams":
            self.x = self.anchor.copy()
        else:
            raise ValueError(f"unknown optimizer kind: {self.kind}")
        return self.x

    def step(self, grad: np.ndarray) -> None:
        if self.kind in {"gd", "ogd"}:
            self.anchor = project_simplex(self.anchor + self.eta * grad)
        elif self.kind in {"rm", "prm"}:
            self.regret = self.regret + grad - float(np.dot(grad, self.x))
        elif self.kind in {"rm_plus", "prm_plus"}:
            self.regret = np.maximum(self.regret + grad - float(np.dot(grad, self.x)), 0.0)
        elif self.kind == "ams":
            self.t += 1
            self.m = self.beta1 * self.m + (1.0 - self.beta1) * grad
            self.v = self.beta2 * self.v + (1.0 - self.beta2) * (grad * grad)
            self.vhat = np.maximum(self.vhat, self.v)
            mhat = self.m / (1.0 - self.beta1**self.t)
            direction = mhat / (np.sqrt(self.vhat) + self.eps)
            self.anchor = project_simplex(self.anchor + self.eta * direction)


def make_optimizer(kind: str, x: np.ndarray, eta: float) -> LocalOptimizer:
    return LocalOptimizer(kind=kind, x=x.copy(), eta=eta)
