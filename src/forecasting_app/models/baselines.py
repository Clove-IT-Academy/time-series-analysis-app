import numpy as np

from .base import Prediction


def baseline_prediction(name, train, steps, season):
    points = (
        np.repeat(train.iloc[-1], steps)
        if name == "Naive"
        else np.resize(train.iloc[-season:].to_numpy(), steps)
    )
    return Prediction(points.astype(float))
