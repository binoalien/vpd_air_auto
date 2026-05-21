"""Entity planning service for VPD Air Auto."""

from __future__ import annotations

from ..const import (
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
)
from ..models import DeviceTopology
from ..policy.models import EffectiveDevicePolicy


class EntityPlanService:
    """Resolve enabled and creatable sensor kinds for discovered devices."""

    @staticmethod
    def enabled_kinds_for_policy(policy: EffectiveDevicePolicy) -> set[str]:
        """Return enabled sensor kinds from an effective policy."""
        enabled_kinds: set[str] = set()
        if policy.enable_air:
            enabled_kinds.add(SENSOR_KIND_AIR)
        if policy.enable_leaf:
            enabled_kinds.add(SENSOR_KIND_LEAF)
        if policy.enable_absolute_humidity:
            enabled_kinds.add(SENSOR_KIND_ABSOLUTE_HUMIDITY)
        if policy.enable_dew_point:
            enabled_kinds.add(SENSOR_KIND_DEW_POINT)
        return enabled_kinds

    def creatable_kinds_for_topology(
        self,
        topology: DeviceTopology | None,
        policy: EffectiveDevicePolicy,
    ) -> set[str]:
        """Return policy-enabled kinds minus blocked kinds for one topology."""
        if topology is None:
            return set()
        return self.enabled_kinds_for_policy(policy).difference(
            topology.blocked_sensor_kinds
        )
