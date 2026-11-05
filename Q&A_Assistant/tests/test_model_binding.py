from __future__ import annotations

import pytest

from qa_assistant.model_binding import InferenceBindingValidator
from qa_contracts.errors import FeatureNotImplemented
from qa_contracts.models import InferenceBinding, InferencePolicy, ModelRole


def test_binding_validation_is_explicitly_unimplemented() -> None:
    binding = InferenceBinding(binding_id="binding-1", policy=InferencePolicy.LOCAL_ONLY)

    with pytest.raises(FeatureNotImplemented):
        InferenceBindingValidator().validate(binding)


def test_missing_model_role_is_not_silently_accepted() -> None:
    binding = InferenceBinding(binding_id="binding-1", policy=InferencePolicy.LOCAL_ONLY)

    with pytest.raises(FeatureNotImplemented):
        InferenceBindingValidator().require_role(binding, ModelRole.GENERATOR)
