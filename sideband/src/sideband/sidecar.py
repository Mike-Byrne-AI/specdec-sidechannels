"""Sidecar classifier: slot multi-hot -> concept.

A deliberately small model (multinomial logistic regression trained with
Adam, numpy only). Rationale:
- the point of the sidecar is that it must be TINY (microseconds per call on
  a memory device's companion logic), so a linear probe is the honest first
  model — if a linear probe on slot sets already recovers the concept, the
  hardware story gets easier, not harder;
- numpy keeps the testbed dependency-free; a 1D-CNN torch variant is a
  drop-in later if slot ORDER/history features are added (see BLUEPRINT
  Phase 3 stretch goals).

Deterministic given seed. Gradient correctness is finite-difference tested.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .dists import Array, softmax


@dataclass
class TrainReport:
    losses: list[float]
    train_acc: float


class SoftmaxRegression:
    def __init__(self, n_features: int, n_classes: int, seed: int = 0):
        gen = np.random.default_rng(seed)
        self.W = gen.normal(0.0, 0.01, size=(n_features, n_classes))
        self.b = np.zeros(n_classes)
        self._seed = seed

    # --- forward / loss ---
    def probs(self, X: Array) -> Array:
        return softmax(X @ self.W + self.b, axis=1)

    def loss_and_grads(self, X: Array, y: Array, l2: float = 0.0):
        n = X.shape[0]
        P = self.probs(X)
        eps = 1e-12
        loss = -np.log(np.clip(P[np.arange(n), y], eps, None)).mean() + 0.5 * l2 * (self.W ** 2).sum()
        G = P.copy()
        G[np.arange(n), y] -= 1.0
        G /= n
        dW = X.T @ G + l2 * self.W
        db = G.sum(axis=0)
        return float(loss), dW, db

    # --- training ---
    def fit(
        self,
        X: Array,
        y: Array,
        epochs: int = 30,
        batch_size: int = 256,
        lr: float = 0.05,
        l2: float = 1e-5,
    ) -> TrainReport:
        gen = np.random.default_rng(self._seed + 1)
        n = X.shape[0]
        mW = np.zeros_like(self.W); vW = np.zeros_like(self.W)
        mb = np.zeros_like(self.b); vb = np.zeros_like(self.b)
        b1, b2, eps = 0.9, 0.999, 1e-8
        step = 0
        losses: list[float] = []
        for _ in range(epochs):
            order = gen.permutation(n)
            epoch_loss = 0.0
            for start in range(0, n, batch_size):
                idx = order[start : start + batch_size]
                loss, dW, db = self.loss_and_grads(X[idx], y[idx], l2=l2)
                epoch_loss += loss * len(idx)
                step += 1
                for param, grad, m, v in ((self.W, dW, mW, vW), (self.b, db, mb, vb)):
                    m *= b1; m += (1 - b1) * grad
                    v *= b2; v += (1 - b2) * grad * grad
                    mhat = m / (1 - b1 ** step)
                    vhat = v / (1 - b2 ** step)
                    param -= lr * mhat / (np.sqrt(vhat) + eps)
            losses.append(epoch_loss / n)
        return TrainReport(losses=losses, train_acc=self.accuracy(X, y))

    # --- inference ---
    def predict(self, X: Array) -> Array:
        return self.probs(X).argmax(axis=1)

    def predict_one(self, x: Array) -> tuple[int, float]:
        """(argmax class, confidence) for a single feature vector."""
        p = softmax((x[None, :] @ self.W + self.b), axis=1)[0]
        c = int(p.argmax())
        return c, float(p[c])

    def accuracy(self, X: Array, y: Array) -> float:
        return float((self.predict(X) == y).mean())
