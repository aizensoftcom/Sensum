from __future__ import annotations

from typing import Any
from collections.abc import Callable

from .sensors.base import Sensor


SensorFactory = Callable[..., Sensor]


class PluginRegistry:
    """In-process registry for sensor factories.

    Packaging/discovery can later be backed by Python entry points without changing this API.
    """

    def __init__(self) -> None:
        self._sensors: dict[str, SensorFactory] = {}

    def register_sensor(self, name: str, factory: SensorFactory) -> None:
        key = name.strip().lower()
        if not key:
            raise ValueError("plugin name must not be empty")
        if key in self._sensors:
            raise ValueError(f"sensor plugin already registered: {key}")
        self._sensors[key] = factory

    def sensor(self, name: str, **kwargs: Any) -> Sensor:
        key = name.strip().lower()
        try:
            factory = self._sensors[key]
        except KeyError as exc:
            raise KeyError(f"unknown sensor plugin: {key}") from exc
        return factory(**kwargs)

    def sensor_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._sensors))


registry = PluginRegistry()
