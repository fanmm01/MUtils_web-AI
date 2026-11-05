"""Consumer contract tests: a client can build every frozen request without A2.

These tests never import a QA core module; they prove the shared Ts/Py clients can
be generated and used against the frozen schema alone.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from qa_contracts.answers import AskRequest, SearchRequest, SubmitAnswer
from qa_contracts.models import DiscoveryRequest, InstallConfirmation
from qa_contracts.selection import SelectionPreviewRequest, UpdateSessionSelection
from tests.contracts.fixtures import REQUEST_FIXTURES, load_fixture

MODEL_BY_PATH = {
    "/v1/search": SearchRequest,
    "/v1/ask": AskRequest,
    "/v1/sessions/session_123/selection": UpdateSessionSelection,
    "/v1/models/discovery": DiscoveryRequest,
    "/v1/model-installs": InstallConfirmation,
    "/v1/knowledge-selection/preview": SelectionPreviewRequest,
    "/v1/sessions/session_123/answers": SubmitAnswer,
}


@pytest.mark.parametrize("fixture_name", REQUEST_FIXTURES)
def test_consumer_can_construct_request(fixture_name: str) -> None:
    fixture = load_fixture(fixture_name)
    model = MODEL_BY_PATH[str(fixture["path"])]
    parsed = model.model_validate(fixture["body"])
    dumped = parsed.model_dump(mode="json", exclude_none=True)
    assert isinstance(dumped, dict)
    assert json.dumps(dumped)


def test_consumer_sees_rejection_for_unknown_fields() -> None:
    fixture = load_fixture("discovery_with_url.json")
    with pytest.raises(ValidationError):
        DiscoveryRequest.model_validate(fixture["body"])


def test_install_confirmation_is_the_only_install_input() -> None:
    fields = set(InstallConfirmation.model_fields)
    assert fields == {"preview_id", "preview_hash", "confirmed"}
    for forbidden in ("url", "model_ref", "target", "path"):
        assert forbidden not in fields


def test_selection_request_overrides_do_not_require_a_session_field() -> None:
    """A one-off selection is expressed inside the ask/search body itself."""
    assert "selection" in AskRequest.model_fields
    assert "selection" in SearchRequest.model_fields
    assert "session_id" in AskRequest.model_fields
