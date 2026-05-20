"""Resolver for effective device policies."""

from __future__ import annotations

from .models import EffectiveDevicePolicy, ScopedPolicyOverride
from .repository import PolicyRepository


class PolicyResolver:
    """Resolve effective policy values for one device/area context."""

    def __init__(self, repository: PolicyRepository) -> None:
        self._repository = repository

    def resolve(self, *, device_id: str, area_id: str | None = None) -> EffectiveDevicePolicy:
        """Resolve effective policy with priority Device > Area > Global."""
        global_policy = self._repository.global_policy
        area_override = self._repository.area_policies.get(area_id or "")
        device_override = self._repository.device_policies.get(device_id)

        return EffectiveDevicePolicy(
            enable_air=self._pick_bool(
                device_override,
                area_override,
                global_policy.enable_air,
                "enable_air",
            ),
            enable_leaf=self._pick_bool(
                device_override,
                area_override,
                global_policy.enable_leaf,
                "enable_leaf",
            ),
            enable_absolute_humidity=self._pick_bool(
                device_override,
                area_override,
                global_policy.enable_absolute_humidity,
                "enable_absolute_humidity",
            ),
            enable_dew_point=self._pick_bool(
                device_override,
                area_override,
                global_policy.enable_dew_point,
                "enable_dew_point",
            ),
            leaf_offset_c=self._pick_float(
                device_override,
                area_override,
                global_policy.leaf_offset_c,
                "leaf_offset_c",
            ),
            display=global_policy.display,
            source_override=self._repository.source_overrides.get(device_id),
        )

    def _pick_bool(
        self,
        device: ScopedPolicyOverride | None,
        area: ScopedPolicyOverride | None,
        default: bool,
        field: str,
    ) -> bool:
        if device is not None and getattr(device, field) is not None:
            return bool(getattr(device, field))
        if area is not None and getattr(area, field) is not None:
            return bool(getattr(area, field))
        return default

    def _pick_float(
        self,
        device: ScopedPolicyOverride | None,
        area: ScopedPolicyOverride | None,
        default: float,
        field: str,
    ) -> float:
        if device is not None and getattr(device, field) is not None:
            return float(getattr(device, field))
        if area is not None and getattr(area, field) is not None:
            return float(getattr(area, field))
        return default
