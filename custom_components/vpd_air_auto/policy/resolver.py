"""Resolve effective per-device policy from global + scoped overrides."""

from __future__ import annotations

from .models import EffectiveDevicePolicy, ScopedPolicyOverride
from .repository import PolicyRepository


class PolicyResolver:
    """Compute effective device policy with Device > Area > Global priority."""

    def __init__(self, repository: PolicyRepository) -> None:
        self._repository = repository

    def resolve_for_device(
        self, device_id: str, area_id: str | None = None
    ) -> EffectiveDevicePolicy:
        global_policy = self._repository.global_policy
        area_override = self._repository.area_policies.get(area_id or "")
        device_override = self._repository.device_policies.get(device_id)

        return EffectiveDevicePolicy(
            enable_air=_resolve_bool(
                global_policy.enable_air, area_override, device_override, "enable_air"
            ),
            enable_leaf=_resolve_bool(
                global_policy.enable_leaf, area_override, device_override, "enable_leaf"
            ),
            enable_absolute_humidity=_resolve_bool(
                global_policy.enable_absolute_humidity,
                area_override,
                device_override,
                "enable_absolute_humidity",
            ),
            enable_dew_point=_resolve_bool(
                global_policy.enable_dew_point,
                area_override,
                device_override,
                "enable_dew_point",
            ),
            leaf_offset_c=_resolve_float(
                global_policy.leaf_offset_c,
                area_override,
                device_override,
                "leaf_offset_c",
            ),
            display=global_policy.display,
            source_override=self._repository.source_overrides.get(device_id),
        )


def _resolve_bool(
    default: bool,
    area_override: ScopedPolicyOverride | None,
    device_override: ScopedPolicyOverride | None,
    field: str,
) -> bool:
    device_value = getattr(device_override, field) if device_override else None
    if device_value is not None:
        return device_value
    area_value = getattr(area_override, field) if area_override else None
    if area_value is not None:
        return area_value
    return default


def _resolve_float(
    default: float,
    area_override: ScopedPolicyOverride | None,
    device_override: ScopedPolicyOverride | None,
    field: str,
) -> float:
    device_value = getattr(device_override, field) if device_override else None
    if device_value is not None:
        return device_value
    area_value = getattr(area_override, field) if area_override else None
    if area_value is not None:
        return area_value
    return default
