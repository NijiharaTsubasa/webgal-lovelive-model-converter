"""Keep short model metadata visible before large facial tables in JSON."""

from __future__ import annotations

from typing import Any


MODEL_HEADER = (
    "type", "name", "description", "group", "role", "model",
    "motionGroup", "humanoidScale", "defaultMotion", "idlePose", "defaultExpression",
)


def order_model_component(component: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: component[key] for key in MODEL_HEADER if key in component},
        **{key: value for key, value in component.items() if key not in MODEL_HEADER},
    }
