"""Entity planning service for creatable sensor kinds."""

from __future__ import annotations

from ..const import (
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
    IntegrationOptions,
)
from ..models import DeviceTopology


class EntityPlanService:
    """Resolve enabled and creatable sensor kinds for a topology."""

    def __init__(self, options: IntegrationOptions) -> None:
        """Initialize the service with resolved integration options."""
        self._options = options

    def enabled_kinds(self) -> set[str]:
        """Return all globally enabled sensor kinds."""
        enabled: set[str] = set()
        if self._options.enable_air:
            enabled.add(SENSOR_KIND_AIR)
        if self._options.enable_leaf:
            enabled.add(SENSOR_KIND_LEAF)
        if self._options.enable_absolute_humidity:
            enabled.add(SENSOR_KIND_ABSOLUTE_HUMIDITY)
        if self._options.enable_dew_point:
            enabled.add(SENSOR_KIND_DEW_POINT)
        return enabled

    def creatable_kinds_for_topology(
        self,
        topology: DeviceTopology | None,
    ) -> set[str]:
        """Return enabled kinds minus kinds blocked by duplicate detection."""
        if topology is None:
            return set()

        return self.enabled_kinds().difference(topology.blocked_sensor_kinds)
