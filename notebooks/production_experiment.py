"""Synthetic material record and public Study setup used by Chapter 10."""

import numpy as np
import pandas as pd
import torch
from botorch.acquisition.analytic import LogExpectedImprovement
from botorch.models.transforms.input import Normalize
from botorch.models.transforms.outcome import Standardize
from robotorchan.models import SingleTaskGP
from robotorchan.study import TrialState, create_study

from experiment import DTYPE, SEED, material_strength

INPUTS = ("temperature_c", "hold_min")
BOX = {"temperature_c": (140.0, 180.0), "hold_min": (10.0, 40.0)}
BOUNDS = torch.tensor(list(BOX.values()), dtype=DTYPE).T
MEASUREMENT_SD_MPA = 1.0


def strength_mean(conditions):
    """Synthetic true mean in MPa. It is only used by the test simulator."""
    temperature, hold = conditions.unbind(dim=-1)
    x = (temperature - 140) / 40
    preferred_hold = 23 + 8 * (x - 0.25)
    return material_strength(x) + 2.5 - 0.035 * (hold - preferred_hold).square()


def measure(conditions, generator):
    mean = strength_mean(conditions)
    return mean + MEASUREMENT_SD_MPA * torch.randn(
        mean.shape, generator=generator, dtype=DTYPE
    )


def historical_log():
    """Create nine example records in acquisition order, including one failure."""
    settings = torch.tensor([
        [140, 10], [144, 34], [149, 17], [152, 33], [156, 24],
        [162, 13], [168, 29], [175, 37], [180, 22],
    ], dtype=DTYPE)
    generator = torch.Generator().manual_seed(SEED + 100)
    result = pd.DataFrame(settings.numpy(), columns=INPUTS)
    result["experiment_id"] = [f"H{i + 1:02d}" for i in range(len(settings))]
    result["lot"] = "SIM-A"
    result["status"] = "COMPLETE"
    result["strength_mpa"] = measure(settings, generator).numpy()
    result["failure_reason"] = ""
    result.loc[5, ["status", "strength_mpa", "failure_reason"]] = [
        "FAIL", np.nan, "模擬計測器のタイムアウト",
    ]
    return result[["experiment_id", "lot", *INPUTS, "status", "strength_mpa", "failure_reason"]]


def validate_history(frame):
    """Validate this chapter's table schema before any trials are registered."""
    columns = ["experiment_id", "lot", *INPUTS, "status", "strength_mpa", "failure_reason"]
    clean = frame.loc[:, columns].copy()
    for name in ["experiment_id", "lot"]:
        if clean[name].isna().any() or clean[name].astype(str).str.strip().eq("").any():
            raise ValueError(f"{name} must be present")
    if clean["experiment_id"].duplicated().any():
        raise ValueError("experiment_id must be unique")
    for name, (low, high) in BOX.items():
        clean[name] = pd.to_numeric(clean[name], errors="raise")
        if not clean[name].between(low, high).all():
            raise ValueError(f"{name} must be within [{low}, {high}]")
    clean["strength_mpa"] = pd.to_numeric(clean["strength_mpa"], errors="raise")
    if not clean["status"].isin(["COMPLETE", "FAIL"]).all():
        raise ValueError("Historical status must be COMPLETE or FAIL")
    complete = clean["status"].eq("COMPLETE")
    if not np.isfinite(clean.loc[complete, "strength_mpa"]).all():
        raise ValueError("Completed rows must have finite strength")
    if clean.loc[~complete, "strength_mpa"].notna().any():
        raise ValueError("Failed rows must have missing strength")
    if clean.loc[~complete, "failure_reason"].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError("Failed rows must have a reason")
    return clean


def model_transforms():
    """Fit inputs in the declared box and return predictions in physical units."""
    return {
        "input_transform": Normalize(d=len(INPUTS), bounds=BOUNDS),
        "outcome_transform": Standardize(m=1),
    }


def new_study():
    return create_study(
        search_space=BOX,
        direction="maximize",
        model=SingleTaskGP,
        model_kwargs=model_transforms(),
        acquisition=LogExpectedImprovement,
        n_initial_trials=5,
        seed=SEED,
        optimizer_kwargs={"num_restarts": 6, "raw_samples": 64, "options": {"seed": SEED}},
    )


def register_history(study, frame):
    """Use public Trial transitions; retain the external ID-to-trial mapping."""
    clean = validate_history(frame)
    metadata = []
    for row in clean.to_dict("records"):
        params = {name: float(row[name]) for name in INPUTS}
        queued = study.add_trial(params)
        running = study.start_trial(queued.number)
        if row["status"] == "COMPLETE":
            study.tell(running, float(row["strength_mpa"]))
        else:
            study.tell(running, state=TrialState.FAIL)
        metadata.append({
            "number": queued.number,
            "experiment_id": row["experiment_id"],
            "lot": row["lot"],
            "failure_reason": row["failure_reason"],
        })
    return pd.DataFrame(metadata)
