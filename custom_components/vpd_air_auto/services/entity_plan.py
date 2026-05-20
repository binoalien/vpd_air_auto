"""Entity planning service for VPD Air Auto."""

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
    """Resolve enabled and creatable sensor kinds for discovered devices."""

    def __init__(self, options: IntegrationOptions) -> None:
        """Initialize the service with resolved integration options."""
        enabled_kinds: set[str] = set()
        if options.enable_air:
            enabled_kinds.add(SENSOR_KIND_AIR)
        if options.enable_leaf:
            enabled_kinds.add(SENSOR_KIND_LEAF)
        if options.enable_absolute_humidity:
            enabled_kinds.add(SENSOR_KIND_ABSOLUTE_HUMIDITY)
        if options.enable_dew_point:
            enabled_kinds.add(SENSOR_KIND_DEW_POINT)
        self._enabled_kinds = frozenset(enabled_kinds)

    def enabled_kinds(self) -> set[str]:
        """Return globally enabled sensor kinds from integration options."""
        return set(self._enabled_kinds)

    def creatable_kinds_for_topology(
        self,
        topology: DeviceTopology | None,
    ) -> set[str]:
        """Return enabled kinds minus blocked kinds for one device topology."""
        if topology is None:
            return set()
        return self.enabled_kinds().difference(topology.blocked_sensor_kinds)
