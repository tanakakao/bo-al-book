"""Shared synthetic pass/fail material test for Chapters 8 and 9."""

import torch
from gpytorch.kernels import MaternKernel, ScaleKernel
from robotorchan.models.classification import BinarySingleTaskGPClassifier

from experiment import DTYPE, NOISE_SD, material_strength

SPEC_MPA = 74.0
FIT_EPOCHS = 60


def pass_probability(x):
    """True simulator probability, reserved for the oracle and evaluation."""
    return torch.special.ndtr((material_strength(x) - SPEC_MPA) / NOISE_SD)


def uniforms(x, seed):
    """Prepare one reproducible independent test draw per temperature."""
    generator = torch.Generator().manual_seed(seed)
    return torch.rand(x.shape, dtype=DTYPE, generator=generator)


def reveal_labels(x, draws):
    """Return only the queried labels from the synthetic destructive test."""
    return (draws < pass_probability(x)).to(DTYPE)


def fit_classifier(train_x, train_y, *, seed, epochs=FIT_EPOCHS):
    """Fit the same full-batch variational GP recipe in both chapters."""
    torch.manual_seed(seed)
    kernel = ScaleKernel(MaternKernel(nu=2.5))
    kernel.base_kernel.lengthscale = 0.18
    inducing = torch.linspace(0, 1, 9, dtype=DTYPE).unsqueeze(-1)
    model = BinarySingleTaskGPClassifier(
        train_x, train_y, covar_module=kernel, inducing_points=inducing,
        learn_inducing_points=False,
    )
    model.fit(epochs=epochs, lr=0.03)
    return model


def bernoulli_entropy(p):
    """Binary entropy in nats, including the endpoint convention 0 log 0 = 0."""
    return -torch.special.xlogy(p, p) - torch.special.xlogy(1 - p, 1 - p)
