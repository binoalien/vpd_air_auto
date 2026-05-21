"""Policy resolution service for effective per-device behavior."""

from __future__ import annotations

from .models import EffectiveDevicePolicy, ScopedPolicyOverride
from .repository import PolicyRepository


class PolicyResolver:  # pylint: disable=too-few-public-methods
    """Resolve effective device policy from global/area/device policy layers."""

    def __init__(self, repository: PolicyRepository) -> None:
        """Store repository dependency."""
        self._repository = repository

    @property
    def repository(self) -> PolicyRepository:
        """Expose policy repository."""
        return self._repository

    def resolve_for_device(
        self,
        *,
        device_id: str,
        area_id: str | None = None,
    ) -> EffectiveDevicePolicy:
        """Resolve effective policy for one device and optional area."""
        global_policy = self._repository.global_policy
        area_override = self._repository.area_policies.get(area_id) if area_id else None
        device_override = self._repository.device_policies.get(device_id)

        return EffectiveDevicePolicy(
            enable_air=self._resolve_bool(
                global_policy.enable_air,
                area_override,
                device_override,
                "enable_air",
            ),
            enable_leaf=self._resolve_bool(
                global_policy.enable_leaf,
                area_override,
                device_override,
                "enable_leaf",
            ),
            enable_absolute_humidity=self._resolve_bool(
                global_policy.enable_absolute_humidity,
                area_override,
                device_override,
                "enable_absolute_humidity",
            ),
            enable_dew_point=self._resolve_bool(
                global_policy.enable_dew_point,
                area_override,
                device_override,
                "enable_dew_point",
            ),
            leaf_offset_c=self._resolve_leaf_offset(
                global_policy.leaf_offset_c,
                area_override,
                device_override,
            ),
            display=global_policy.display,
            source_override=self._repository.source_overrides.get(device_id),
            behavior_source=self._resolve_behavior_source(
                area_override,
                device_override,
            ),
            leaf_offset_source=self._resolve_leaf_offset_source(
                area_override,
                device_override,
            ),
        )

    def resolve_for_device_area_only(
        self,
        *,
        device_id: str,
        area_id: str | None = None,
    ) -> EffectiveDevicePolicy:
        """Resolve effective policy using only global + area overrides."""
        global_policy = self._repository.global_policy
        area_override = self._repository.area_policies.get(area_id) if area_id else None

        return EffectiveDevicePolicy(
            enable_air=self._resolve_bool(
                global_policy.enable_air,
                area_override,
                None,
                "enable_air",
            ),
            enable_leaf=self._resolve_bool(
                global_policy.enable_leaf,
                area_override,
                None,
                "enable_leaf",
            ),
            enable_absolute_humidity=self._resolve_bool(
                global_policy.enable_absolute_humidity,
                area_override,
                None,
                "enable_absolute_humidity",
            ),
            enable_dew_point=self._resolve_bool(
                global_policy.enable_dew_point,
                area_override,
                None,
                "enable_dew_point",
            ),
            leaf_offset_c=self._resolve_leaf_offset(
                global_policy.leaf_offset_c,
                area_override,
                None,
            ),
            display=global_policy.display,
            source_override=self._repository.source_overrides.get(device_id),
            behavior_source=self._resolve_behavior_source(area_override, None),
            leaf_offset_source=self._resolve_leaf_offset_source(area_override, None),
        )

    @staticmethod
    def _resolve_bool(
        default: bool,
        area: ScopedPolicyOverride | None,
        device: ScopedPolicyOverride | None,
        field: str,
    ) -> bool:
        if device is not None and getattr(device, field) is not None:
            return bool(getattr(device, field))
        if area is not None and getattr(area, field) is not None:
            return bool(getattr(area, field))
        return default

    @staticmethod
    def _resolve_leaf_offset(
        default: float,
        area: ScopedPolicyOverride | None,
        device: ScopedPolicyOverride | None,
    ) -> float:
        if device is not None and device.leaf_offset_c is not None:
            return device.leaf_offset_c
        if area is not None and area.leaf_offset_c is not None:
            return area.leaf_offset_c
        return default

    @staticmethod
    def _resolve_behavior_source(
        area: ScopedPolicyOverride | None,
        device: ScopedPolicyOverride | None,
    ) -> str:
        behavior_fields = (
            "enable_air",
            "enable_leaf",
            "enable_absolute_humidity",
            "enable_dew_point",
        )
        if device and any(
            getattr(device, field) is not None for field in behavior_fields
        ):
            return "device"
        if area and any(
            getattr(area, field) is not None for field in behavior_fields
        ):
            return "area"
        return "global"

    @staticmethod
    def _resolve_leaf_offset_source(
        area: ScopedPolicyOverride | None,
        device: ScopedPolicyOverride | None,
    ) -> str:
        if device and device.leaf_offset_c is not None:
            return "device"
        if area and area.leaf_offset_c is not None:
            return "area"
        return "global"
