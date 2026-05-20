from .models import EffectiveDevicePolicy, ScopedPolicyOverride
from .repository import PolicyRepository


class PolicyResolver:
    def __init__(self, repository: PolicyRepository) -> None:
        self._repository = repository

    def resolve_for_device(self, device_id: str, area_id: str | None = None) -> EffectiveDevicePolicy:
        global_policy = self._repository.global_policy
        area_override = self._repository.area_policies.get(area_id or "")
        device_override = self._repository.device_policies.get(device_id)
        return EffectiveDevicePolicy(
            enable_air=self._resolve("enable_air", global_policy.enable_air, area_override, device_override),
            enable_leaf=self._resolve("enable_leaf", global_policy.enable_leaf, area_override, device_override),
            enable_absolute_humidity=self._resolve("enable_absolute_humidity", global_policy.enable_absolute_humidity, area_override, device_override),
            enable_dew_point=self._resolve("enable_dew_point", global_policy.enable_dew_point, area_override, device_override),
            leaf_offset_c=self._resolve("leaf_offset_c", global_policy.leaf_offset_c, area_override, device_override),
            display=global_policy.display,
            source_override=self._repository.source_overrides.get(device_id),
        )

    @staticmethod
    def _resolve(name: str, default, area_override: ScopedPolicyOverride | None, device_override: ScopedPolicyOverride | None):
        if device_override is not None and getattr(device_override, name) is not None:
            return getattr(device_override, name)
        if area_override is not None and getattr(area_override, name) is not None:
            return getattr(area_override, name)
        return default
