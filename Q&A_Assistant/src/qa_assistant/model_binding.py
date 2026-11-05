"""Provider-independent inference binding validation placeholder."""

from __future__ import annotations

from qa_contracts.errors import FeatureNotImplemented
from qa_contracts.models import InferenceBinding, ModelRole, RoleBinding


class InferenceBindingValidator:
    """P1 rejects all calls until a persisted, verified binding is available."""

    def validate(self, binding: InferenceBinding) -> None:
        raise FeatureNotImplemented("inference binding validation")

    def require_role(self, binding: InferenceBinding, role: ModelRole) -> RoleBinding:
        raise FeatureNotImplemented(f"inference role binding: {role.value}")
